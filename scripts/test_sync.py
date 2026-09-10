import io
import json
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path
from unittest.mock import patch

if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts import sync
from scripts.sync import (
    CORE_START, CORE_END, TARGETS, SyncError, apply_plans, build_plans,
    deploy_after_pull, extract_core_block, main, parse_args, render_core_block,
    sha256_bytes, sha256_text, sync_all,
)


class SyncFixture(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.repo = self.root / "repo"
        (self.repo / "core" / "skills" / "demo" / "references").mkdir(parents=True)
        (self.repo / "core" / "INSTRUCTIONS.md").write_text("CORE\n", encoding="utf-8")
        (self.repo / "core" / "skills" / "demo" / "SKILL.md").write_text("skill-v1", encoding="utf-8")
        (self.repo / "core" / "skills" / "demo" / "references" / "guide.md").write_text("guide", encoding="utf-8")
        for name, (adapter_rel, _) in TARGETS.items():
            adapter = self.repo / adapter_rel
            adapter.parent.mkdir(parents=True, exist_ok=True)
            adapter.write_text(
                f"# {name}\n\n{CORE_START}\nOLD\n{CORE_END}\n\n## Host notes\n",
                encoding="utf-8",
            )

    def home(self, name: str = "zcode") -> Path:
        return self.root / f"{name}-home"

    def homes(self) -> dict[str, Path]:
        return {name: self.home(name) for name in TARGETS}

    def plans(self, **options):
        arguments = {f"{name}_home": self.home(name) for name in TARGETS}
        arguments.update(target="zcode")
        arguments.update(options)
        return sync_all(self.repo, **arguments)


class TestMarkers(unittest.TestCase):
    def test_valid_markers_update_only_inner_block(self):
        text = f"head\n{CORE_START}\nold\n{CORE_END}\ntail\n"
        result = render_core_block(text, "new")
        self.assertEqual(result, f"head\n{CORE_START}\nnew\n{CORE_END}\ntail\n")

    def test_missing_markers_are_appended_for_source_rendering(self):
        result = render_core_block("head\n", "core")
        self.assertIn(f"{CORE_START}\ncore\n{CORE_END}", result)

    def test_malformed_markers_are_rejected(self):
        with self.assertRaises(SyncError):
            render_core_block(f"{CORE_START}\nold\n", "new")


class TestPlanningAndApply(SyncFixture):
    def test_auto_does_not_create_missing_homes(self):
        plans = sync_all(
            self.repo,
            codex_home=self.home("codex"),
            claude_home=self.home("claude"),
            zcode_home=self.home("zcode"),
            target="auto",
        )
        self.assertEqual(plans, [])
        self.assertFalse(self.home().exists())

    def test_explicit_target_can_create_home_only_on_apply(self):
        plans = sync_all(self.repo, zcode_home=self.home(), target="zcode")
        self.assertEqual(plans[0].entry.action, "create")
        self.assertFalse(self.home().exists())
        sync_all(self.repo, zcode_home=self.home(), target="zcode", apply=True)
        self.assertTrue((self.home() / "AGENTS.md").exists())
        self.assertTrue((self.home() / "skills/demo/SKILL.md").exists())
        self.assertTrue((self.home() / ".agent-kit/manifest.json").exists())

    def test_unmarked_entry_is_backed_up_before_replacement(self):
        home = self.home()
        home.mkdir()
        entry = home / "AGENTS.md"
        entry.write_text("my old rules", encoding="utf-8")
        plans = sync_all(self.repo, zcode_home=home, target="zcode")
        self.assertEqual(plans[0].entry.action, "replace")
        self.assertTrue(plans[0].entry.backup)
        sync_all(self.repo, zcode_home=home, target="zcode", apply=True)
        self.assertIn("CORE", entry.read_text(encoding="utf-8"))
        backups = list((home / ".agent-kit/backups").rglob("AGENTS.md"))
        self.assertEqual(len(backups), 1)
        self.assertEqual(backups[0].read_text(encoding="utf-8"), "my old rules")

    def test_marked_entry_preserves_host_notes(self):
        home = self.home()
        home.mkdir()
        entry = home / "AGENTS.md"
        entry.write_text(f"custom\n{CORE_START}\nold\n{CORE_END}\nnotes\n", encoding="utf-8")
        sync_all(self.repo, zcode_home=home, target="zcode", apply=True, replace=["zcode:AGENTS.md"])
        content = entry.read_text(encoding="utf-8")
        self.assertIn("custom", content)
        self.assertIn("CORE", content)
        self.assertIn("notes", content)

    def test_malformed_entry_stops_without_writing(self):
        home = self.home()
        home.mkdir()
        entry = home / "AGENTS.md"
        entry.write_text(f"{CORE_START}\nold\n", encoding="utf-8")
        with self.assertRaises(SyncError):
            deploy_after_pull(self.repo, codex_home=self.home("codex"), claude_home=self.home("claude"), zcode_home=home, target="zcode", apply=True)
        self.assertEqual(entry.read_text(encoding="utf-8"), f"{CORE_START}\nold\n")
        self.assertFalse((home / "skills").exists())

    def test_unmanaged_matching_skill_is_adopted_without_overwrite(self):
        home = self.home()
        (home / "skills/demo").mkdir(parents=True)
        (home / "skills/demo/SKILL.md").write_text("skill-v1", encoding="utf-8")
        plans = sync_all(self.repo, zcode_home=home, target="zcode")
        actions = {action.rel: action.action for action in plans[0].skills}
        self.assertEqual(actions["skills/demo/SKILL.md"], "adopt")
        sync_all(self.repo, zcode_home=home, target="zcode", apply=True)
        self.assertTrue((home / ".agent-kit/manifest.json").exists())

    def test_unmanaged_different_skill_is_conflict(self):
        home = self.home()
        (home / "skills/demo").mkdir(parents=True)
        (home / "skills/demo/SKILL.md").write_text("user skill", encoding="utf-8")
        plans = sync_all(self.repo, zcode_home=home, target="zcode")
        self.assertTrue(any("Unmanaged skill file differs" in message for message in plans[0].conflicts))
        with self.assertRaises(SyncError):
            sync_all(self.repo, zcode_home=home, target="zcode", apply=True)
        self.assertEqual((home / "skills/demo/SKILL.md").read_text(encoding="utf-8"), "user skill")

    def test_managed_skill_update_preserves_custom_files(self):
        home = self.home()
        sync_all(self.repo, zcode_home=home, target="zcode", apply=True)
        custom = home / "skills/demo/custom.md"
        custom.write_text("keep me", encoding="utf-8")
        (self.repo / "core/skills/demo/SKILL.md").write_text("skill-v2", encoding="utf-8")
        sync_all(self.repo, zcode_home=home, target="zcode", apply=True)
        self.assertEqual((home / "skills/demo/SKILL.md").read_text(encoding="utf-8"), "skill-v2")
        self.assertEqual(custom.read_text(encoding="utf-8"), "keep me")

    def test_managed_user_change_and_source_change_is_conflict(self):
        home = self.home()
        sync_all(self.repo, zcode_home=home, target="zcode", apply=True)
        (home / "skills/demo/SKILL.md").write_text("user edit", encoding="utf-8")
        (self.repo / "core/skills/demo/SKILL.md").write_text("skill-v2", encoding="utf-8")
        plans = sync_all(self.repo, zcode_home=home, target="zcode")
        self.assertTrue(any("source also changed" in message for message in plans[0].conflicts))

    def test_removed_source_is_reported_but_not_deleted(self):
        home = self.home()
        sync_all(self.repo, zcode_home=home, target="zcode", apply=True)
        source = self.repo / "core/skills/demo/references/guide.md"
        source.unlink()
        plans = sync_all(self.repo, zcode_home=home, target="zcode")
        self.assertIn("skills/demo/references/guide.md", plans[0].stale)
        self.assertTrue((home / "skills/demo/references/guide.md").exists())

    def test_all_targets_preflight_is_atomic_on_conflict(self):
        homes = self.homes()
        homes["codex"].mkdir()
        (homes["codex"] / "AGENTS.md").write_text("codex custom", encoding="utf-8")
        homes["zcode"].mkdir()
        (homes["zcode"] / "skills/demo").mkdir(parents=True)
        (homes["zcode"] / "skills/demo/SKILL.md").write_text("zcode custom", encoding="utf-8")
        with self.assertRaises(SyncError):
            deploy_after_pull(self.repo, codex_home=homes["codex"], claude_home=homes["claude"], zcode_home=homes["zcode"], target="all", apply=True)
        self.assertEqual((homes["codex"] / "AGENTS.md").read_text(encoding="utf-8"), "codex custom")
        self.assertFalse((homes["claude"] / "AGENTS.md").exists())
        self.assertEqual((homes["zcode"] / "skills/demo/SKILL.md").read_text(encoding="utf-8"), "zcode custom")
    def test_marked_entry_without_baseline_requires_scoped_replace(self):
        home = self.home()
        home.mkdir()
        entry = home / "AGENTS.md"
        entry.write_text(f"host\n{CORE_START}\nOLD\n{CORE_END}\nnotes\n", encoding="utf-8")
        plans = sync_all(self.repo, zcode_home=home, target="zcode")
        self.assertTrue(any("no matching baseline" in message for message in plans[0].conflicts))
        sync_all(self.repo, zcode_home=home, target="zcode", apply=True, replace=["zcode:AGENTS.md"])
        self.assertIn("CORE", entry.read_text(encoding="utf-8"))
        self.assertEqual(len(list((home / ".agent-kit/backups").rglob("AGENTS.md"))), 1)

    def test_matching_marked_entry_without_manifest_is_adopted(self):
        home = self.home()
        home.mkdir()
        entry = home / "AGENTS.md"
        original = render_core_block("host notes\n", "CORE\n")
        entry.write_bytes(original.encode("utf-8"))
        plans = sync_all(self.repo, zcode_home=home, target="zcode")
        self.assertEqual(plans[0].entry.action, "adopt")
        sync_all(self.repo, zcode_home=home, target="zcode", apply=True)
        self.assertEqual(entry.read_bytes(), original.encode("utf-8"))

    def test_replace_preserves_crlf_bytes_outside_entry_block(self):
        home = self.home()
        sync_all(self.repo, zcode_home=home, target="zcode", apply=True)
        entry = home / "AGENTS.md"
        entry.write_bytes(f"head\r\n{CORE_START}\r\nOLD\r\n{CORE_END}\r\ntail\r\n".encode("utf-8"))
        sync_all(self.repo, zcode_home=home, target="zcode", apply=True, replace=["zcode:AGENTS.md"])
        result = entry.read_bytes()
        self.assertTrue(result.startswith(b"head\r\n"))
        self.assertTrue(result.endswith(b"\r\ntail\r\n"))
        self.assertIn(b"CORE", result)
        self.assertNotIn(b"OLD", result)

    def test_deleted_managed_skill_is_preserved_until_source_changes(self):
        home = self.home()
        sync_all(self.repo, zcode_home=home, target="zcode", apply=True)
        skill = home / "skills/demo/SKILL.md"
        skill.unlink()
        plans = sync_all(self.repo, zcode_home=home, target="zcode")
        actions = {action.rel: action.action for action in plans[0].skills}
        self.assertEqual(actions["skills/demo/SKILL.md"], "preserve")
        sync_all(self.repo, zcode_home=home, target="zcode", apply=True)
        self.assertFalse(skill.exists())
        (self.repo / "core/skills/demo/SKILL.md").write_text("skill-v2", encoding="utf-8")
        plans = sync_all(self.repo, zcode_home=home, target="zcode")
        self.assertTrue(any("changed/deleted skill" in message for message in plans[0].conflicts))
        sync_all(self.repo, zcode_home=home, target="zcode", apply=True, replace=["zcode:skills/demo/SKILL.md"])
        self.assertEqual(skill.read_text(encoding="utf-8"), "skill-v2")

    def test_scoped_skill_replace_backs_up_existing_file(self):
        home = self.home()
        (home / "skills/demo").mkdir(parents=True)
        skill = home / "skills/demo/SKILL.md"
        skill.write_text("local version", encoding="utf-8")
        plans = sync_all(self.repo, zcode_home=home, target="zcode", replace=["zcode:skills/demo/SKILL.md"])
        action = next(item for item in plans[0].skills if item.rel == "skills/demo/SKILL.md")
        self.assertEqual(action.action, "replace")
        self.assertTrue(action.backup)
        sync_all(self.repo, zcode_home=home, target="zcode", apply=True, replace=["zcode:skills/demo/SKILL.md"])
        backups = list((home / ".agent-kit/backups").rglob("SKILL.md"))
        self.assertEqual(len(backups), 1)
        self.assertEqual(backups[0].read_text(encoding="utf-8"), "local version")
        self.assertEqual(skill.read_text(encoding="utf-8"), "skill-v1")

    def test_corrupt_manifest_is_a_conflict(self):
        home = self.home()
        (home / ".agent-kit").mkdir(parents=True)
        (home / ".agent-kit/manifest.json").write_text('{"version": 1, "skills": {}}', encoding="utf-8")
        plans = sync_all(self.repo, zcode_home=home, target="zcode")
        self.assertTrue(any("Malformed manifest" in message for message in plans[0].conflicts))
        self.assertFalse((home / "AGENTS.md").exists())

    def test_destination_snapshot_is_rechecked_before_apply(self):
        home = self.home()
        plans = sync_all(self.repo, zcode_home=home, target="zcode")
        (home / "AGENTS.md").parent.mkdir(parents=True)
        (home / "AGENTS.md").write_text("changed after preview", encoding="utf-8")
        with self.assertRaises(SyncError):
            apply_plans(plans)
        self.assertEqual((home / "AGENTS.md").read_text(encoding="utf-8"), "changed after preview")
        self.assertFalse((home / "skills").exists())

    def test_source_snapshot_is_rechecked_before_apply(self):
        home = self.home()
        plans = sync_all(self.repo, zcode_home=home, target="zcode")
        (self.repo / "core/skills/demo/SKILL.md").write_text("changed after preview", encoding="utf-8")
        with self.assertRaises(SyncError):
            apply_plans(plans)
        self.assertFalse(home.exists())

    def test_runtime_failure_rolls_back_written_files(self):
        home = self.home()
        sync_all(self.repo, zcode_home=home, target="zcode", apply=True)
        old_entry, old_skill = (home / "AGENTS.md").read_bytes(), (home / "skills/demo/SKILL.md").read_bytes()
        (self.repo / "core/INSTRUCTIONS.md").write_text("CORE-v2\n", encoding="utf-8")
        (self.repo / "core/skills/demo/SKILL.md").write_text("skill-v2", encoding="utf-8")
        plans = sync_all(self.repo, zcode_home=home, target="zcode")
        real_write = sync.atomic_write_bytes
        calls = 0

        def fail_on_second(target, content, **kwargs):
            nonlocal calls
            calls += 1
            if calls == 2:
                raise OSError("injected write failure")
            return real_write(target, content, **kwargs)

        with patch.object(sync, "atomic_write_bytes", side_effect=fail_on_second):
            with self.assertRaises(SyncError) as raised:
                apply_plans(plans)
        self.assertIn("restored", str(raised.exception))
        self.assertEqual((home / "AGENTS.md").read_bytes(), old_entry)
        self.assertEqual((home / "skills/demo/SKILL.md").read_bytes(), old_skill)

    def test_overlapping_target_home_is_rejected(self):
        home = self.home()
        plans = build_plans(self.repo, {"zcode": home}, "zcode")
        self.assertFalse(plans[0].conflicts)
        plans = build_plans(self.repo, {"zcode": self.repo / "inside"}, "zcode")
        self.assertTrue(any("overlaps" in message for message in plans[0].conflicts))


class TestCli(SyncFixture):
    def invoke(self, *flags):
        output = io.StringIO()
        arguments = ["--repo", str(self.repo), "--target", "zcode"]
        for name, home in self.homes().items():
            arguments.extend([f"--{name}-home", str(home)])
        with redirect_stdout(output), redirect_stderr(output):
            result = main([*arguments, *flags])
        return result, output.getvalue()

    def test_preview_pull_never_pulls(self):
        for flags in (("--pull",), ("--pull", "--dry-run"), ("--pull", "--force")):
            with self.subTest(flags=flags), patch.object(sync, "pull_repository") as pull:
                result, output = self.invoke(*flags)
                pull.assert_not_called()
                self.assertEqual(result, 0)
                self.assertIn("deferred", output)
                self.assertFalse(self.home().exists())

    def test_apply_and_dry_run_rejected_before_pull(self):
        with patch.object(sync, "pull_repository") as pull, self.assertRaises(SystemExit) as failure:
            self.invoke("--apply", "--dry-run", "--pull")
        self.assertEqual(failure.exception.code, 2)
        pull.assert_not_called()
        with self.assertRaises(SyncError):
            deploy_after_pull(self.repo, codex_home=self.home("codex"), claude_home=self.home("claude"),
                              zcode_home=self.home(), apply=True, dry_run=True, pull=True)
        self.assertFalse(self.home().exists())

    def test_force_alone_never_writes(self):
        result, output = self.invoke("--force")
        self.assertEqual(result, 0)
        self.assertIn("Preview only", output)
        self.assertFalse(self.home().exists())

    def test_pull_failure_stops_unless_forced(self):
        with patch.object(sync, "pull_repository", side_effect=SyncError("offline")):
            result, output = self.invoke("--pull", "--apply")
            self.assertEqual(result, 2)
            self.assertFalse(self.home().exists())
            self.assertNotIn("Sync applied successfully", output)
            result, output = self.invoke("--pull", "--apply", "--force")
            self.assertEqual(result, 0)
            self.assertEqual(output.count("Sync applied successfully"), 1)
        self.assertTrue((self.home() / "AGENTS.md").exists())

    def test_force_never_bypasses_content_conflicts(self):
        path = self.home() / "skills/demo/SKILL.md"
        path.parent.mkdir(parents=True)
        path.write_bytes(b"private skill")
        with patch.object(sync, "pull_repository", side_effect=SyncError("offline")):
            result, output = self.invoke("--pull", "--apply", "--force")
        self.assertEqual(result, 2)
        self.assertNotIn("Sync applied successfully", output)
        self.assertEqual(path.read_bytes(), b"private skill")
        self.assertFalse((self.home() / ".agent-kit").exists())

    def test_invalid_replace_rejected_before_pull(self):
        values = ("all:AGENTS.md", "zcode:../secret", "zcode:/absolute", "zcode:skills/*/SKILL.md",
                  "zcode:skills/demo/../SKILL.md", "zcode:skills\\demo\\SKILL.md", "zcode:.agent-kit/manifest.json",
                  "zcode:skills/demo/x:stream", "zcode:skills/demo/CON", "claude:CLAUDE.md")
        for value in values:
            with self.subTest(value=value), patch.object(sync, "pull_repository") as pull:
                result, output = self.invoke("--replace", value, "--apply", "--pull")
                self.assertEqual(result, 2, output)
                pull.assert_not_called()
                self.assertFalse(self.home().exists())

    def test_typo_in_replacement_is_conflict(self):
        result, output = self.invoke("--replace", "zcode:skills/demo/typo.md", "--apply")
        self.assertEqual(result, 2)
        self.assertIn("not a current source", output)
        self.assertFalse(self.home().exists())

    def test_replacement_is_scoped_repeatable_and_preview_only_by_default(self):
        home = self.home()
        for relative in ("SKILL.md", "references/guide.md"):
            path = home / "skills/demo" / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b"custom")
        replacement = ["--replace", "zcode:skills/demo/SKILL.md"]
        result, output = self.invoke(*replacement, "--apply")
        self.assertEqual(result, 2)
        self.assertIn("references/guide.md", output)
        replacement.extend(["--replace", "zcode:skills/demo/references/guide.md"])
        result, output = self.invoke(*replacement)
        self.assertEqual(result, 0)
        self.assertFalse((home / ".agent-kit").exists())
        result, output = self.invoke(*replacement, "--apply")
        self.assertEqual(result, 0)
        self.assertEqual((home / "skills/demo/SKILL.md").read_bytes(), b"skill-v1")

    def test_failure_does_not_print_success(self):
        with patch.object(sync, "atomic_write_bytes", side_effect=OSError("disk full")):
            result, output = self.invoke("--apply")
        self.assertEqual(result, 2)
        self.assertNotIn("Sync applied successfully", output)
        self.assertFalse(self.home().exists())

    def test_test_runner_returns_failure_exit_code(self):
        with patch.object(sync, "load_tests", return_value=unittest.TestSuite()), \
             patch.object(sync.unittest, "TextTestRunner") as runner:
            runner.return_value.run.return_value.wasSuccessful.return_value = False
            self.assertEqual(main(["test"]), 1)

    def test_default_is_preview(self):
        output = tempfile.TemporaryFile(mode="w+", encoding="utf-8")
        try:
            with patch(f"{sync.__name__}.pull_repository") as pull, redirect_stdout(output):
                result = main(["--repo", str(self.repo), "--target", "zcode", "--zcode-home", str(self.home())])
            pull.assert_not_called()
            self.assertEqual(result, 0)
            self.assertFalse(self.home().exists())
        finally:
            output.close()

    def test_apply_flag_writes_and_pull_is_explicit(self):
        with patch(f"{sync.__name__}.pull_repository") as pull:
            result = main(["--repo", str(self.repo), "--target", "zcode", "--zcode-home", str(self.home()), "--apply"])
        pull.assert_not_called()
        self.assertEqual(result, 0)
        self.assertTrue((self.home() / "AGENTS.md").exists())

    def test_pull_flag_calls_pull(self):
        with patch(f"{sync.__name__}.pull_repository", return_value=False) as pull:
            result = main(["--repo", str(self.repo), "--target", "zcode", "--zcode-home", str(self.home()), "--apply", "--pull"])
        pull.assert_called_once_with(self.repo)
        self.assertEqual(result, 0)
        self.assertTrue(self.home().exists())


class TestSafetyEdges(SyncFixture):
    def test_all_backups_are_verified_before_any_configuration_write(self):
        originals = {}
        for name, home in self.homes().items():
            home.mkdir()
            path = home / TARGETS[name][1]
            path.write_bytes(f"old {name}".encode())
            originals[path] = path.read_bytes()
        plans = self.plans(target="all")

        def corrupt_backup(source, backup, expected):
            backup.write_bytes(b"broken backup")

        with patch.object(sync, "backup_file", side_effect=corrupt_backup), \
             patch.object(sync, "atomic_write_bytes") as write, self.assertRaises(SyncError):
            apply_plans(plans)
        write.assert_not_called()
        for path, original in originals.items():
            self.assertEqual(path.read_bytes(), original)
            self.assertFalse((path.parent / "skills").exists())
            self.assertFalse((path.parent / ".agent-kit/sync.lock").exists())

    def test_backup_failure_stops_all_targets(self):
        self.home().mkdir()
        entry = self.home() / "AGENTS.md"
        entry.write_bytes(b"old rules")
        plans = self.plans(target="all")
        with patch.object(sync, "backup_file", side_effect=OSError("backup disk full")), self.assertRaises(SyncError):
            apply_plans(plans)
        self.assertEqual(entry.read_bytes(), b"old rules")
        self.assertFalse(self.home("codex").exists())
        self.assertFalse(self.home("claude").exists())

    def test_last_manifest_failure_restores_every_target(self):
        self.plans(target="all", apply=True)
        originals = {path: path.read_bytes() for home in self.homes().values() for path in home.rglob("*") if path.is_file()}
        (self.repo / "core/INSTRUCTIONS.md").write_bytes(b"CORE v2")
        (self.repo / "core/skills/demo/SKILL.md").write_bytes(b"skill-v2")
        plans = self.plans(target="all")
        blocked = plans[-1].manifest
        write = sync.atomic_write_bytes

        def fail_last_manifest(target, content, **kwargs):
            if target == blocked.destination and content == blocked.content:
                raise OSError("manifest write failed")
            write(target, content, **kwargs)

        with patch.object(sync, "atomic_write_bytes", side_effect=fail_last_manifest), self.assertRaisesRegex(SyncError, "restored"):
            apply_plans(plans)
        for path, original in originals.items():
            self.assertEqual(path.read_bytes(), original, str(path))
        self.assertFalse(any(home.joinpath(".agent-kit/sync.lock").exists() for home in self.homes().values()))

    def test_failed_rollback_reports_backup_location(self):
        home = self.home()
        home.mkdir()
        entry = home / "AGENTS.md"
        entry.write_bytes(b"old rules")
        plans = self.plans()
        write = sync.atomic_write_bytes

        def fail_writes_and_restore(target, content, **kwargs):
            if target != entry or content == b"old rules":
                raise OSError("injected failure")
            write(target, content, **kwargs)

        with patch.object(sync, "atomic_write_bytes", side_effect=fail_writes_and_restore), self.assertRaises(SyncError) as error:
            apply_plans(plans)
        self.assertIn("Rollback incomplete", str(error.exception))
        self.assertIn(str(plans[0].backup_root), str(error.exception))
        self.assertEqual((plans[0].backup_root / "AGENTS.md").read_bytes(), b"old rules")

    def test_rollback_does_not_overwrite_external_edits(self):
        plans = self.plans()
        entry = self.home() / "AGENTS.md"
        write = sync.atomic_write_bytes

        def change_entry_before_failure(target, content, **kwargs):
            if target != entry:
                entry.write_bytes(b"concurrent edit")
                raise OSError("failure after concurrent edit")
            write(target, content, **kwargs)

        with patch.object(sync, "atomic_write_bytes", side_effect=change_entry_before_failure), self.assertRaisesRegex(SyncError, "Rollback incomplete"):
            apply_plans(plans)
        self.assertEqual(entry.read_bytes(), b"concurrent edit")

    def test_malformed_markers_cannot_be_waived(self):
        home = self.home()
        home.mkdir()
        entry = home / "AGENTS.md"
        valid = f"{CORE_START}\nCORE\n{CORE_END}"
        texts = (CORE_START, CORE_END, f"{CORE_END}\n{CORE_START}", valid * 2,
                 valid + "\n<!-- AGENT-KIT:CORE:START", "<!-- AGENT-KIT:CORE:END")
        for text in texts:
            with self.subTest(text=text):
                entry.write_bytes(text.encode())
                plans = self.plans(replace=["zcode:AGENTS.md"])
                self.assertTrue(plans[0].conflicts)
                with self.assertRaises(SyncError):
                    apply_plans(plans)
                self.assertEqual(entry.read_bytes(), text.encode())
                self.assertFalse((home / ".agent-kit").exists())

    def test_unreadable_entry_cannot_bypass_marker_protection(self):
        home = self.home()
        home.mkdir()
        entry = home / "AGENTS.md"
        for content in (CORE_START.encode("utf-16"), CORE_START.encode("utf-16-le"), b"\xffunknown encoding"):
            with self.subTest(content=content):
                entry.write_bytes(content)
                self.assertTrue(self.plans(replace=["zcode:AGENTS.md"])[0].conflicts)
                self.assertEqual(entry.read_bytes(), content)

    def test_manifest_validation_rejects_invalid_baselines_and_paths(self):
        valid = {"version": 1, "target": "zcode", "entry": {"path": "AGENTS.md", "core_sha256": "a" * 64}, "skills": {"demo/SKILL.md": "b" * 64}}
        cases = [dict(valid, version=True), dict(valid, version=2), dict(valid, target="codex"),
                 dict(valid, target=None), dict(valid, extra="unknown"), dict(valid, skills=[]),
                 dict(valid, entry={"path": "../AGENTS.md", "core_sha256": "a" * 64}),
                 dict(valid, entry={"path": "AGENTS.md", "core_sha256": "invalid"})]
        for path in ("../outside", "/absolute", "demo/../../out", "C:/outside", "demo\\SKILL.md",
                     "demo//SKILL.md", "demo/./SKILL.md", "demo/stream:foo", "demo/NUL", "demo/trailing."):
            cases.append(dict(valid, skills={path: "b" * 64}))
        cases.append(dict(valid, skills={"demo/SKILL.md": 12}))
        home = self.home()
        (home / ".agent-kit").mkdir(parents=True)
        manifest = home / ".agent-kit/manifest.json"
        payloads = [json.dumps(case).encode() for case in cases]
        payloads.extend((b"null", b"[]", b"{", b'{"version":1,"version":1}', b"\xff"))
        for payload in payloads:
            with self.subTest(payload=payload):
                manifest.write_bytes(payload)
                plans = self.plans(replace=["zcode:AGENTS.md", "zcode:skills/demo/SKILL.md"])
                self.assertTrue(plans[0].conflicts)
                with self.assertRaises(SyncError):
                    apply_plans(plans)
                self.assertEqual(manifest.read_bytes(), payload)
                self.assertFalse((home / "AGENTS.md").exists())

    def test_source_core_adapter_and_file_list_changes_abort(self):
        paths = (self.repo / "core/INSTRUCTIONS.md", self.repo / TARGETS["zcode"][0], self.repo / "core/skills/demo/new.md")
        for path in paths:
            with self.subTest(path=path):
                original = path.read_bytes() if path.exists() else None
                plans = self.plans()
                path.write_bytes(b"changed source")
                with self.assertRaises(SyncError):
                    apply_plans(plans)
                self.assertFalse(self.home().exists())
                if original is None:
                    path.unlink()
                else:
                    path.write_bytes(original)

    def test_manifest_changed_after_planning_aborts(self):
        self.plans(apply=True)
        (self.repo / "core/INSTRUCTIONS.md").write_bytes(b"new core")
        plans = self.plans()
        manifest = self.home() / ".agent-kit/manifest.json"
        entry_before = (self.home() / "AGENTS.md").read_bytes()
        manifest.write_bytes(manifest.read_bytes() + b" ")
        with self.assertRaises(SyncError):
            apply_plans(plans)
        self.assertEqual((self.home() / "AGENTS.md").read_bytes(), entry_before)
        self.assertFalse((self.home() / ".agent-kit/backups").exists())

    def test_destination_changed_during_backup_aborts(self):
        home = self.home()
        home.mkdir()
        entry = home / "AGENTS.md"
        entry.write_bytes(b"old")
        plans = self.plans()
        backup = sync.backup_file

        def change_after_backup(source, destination, expected):
            backup(source, destination, expected)
            source.write_bytes(b"new external edit")

        with patch.object(sync, "backup_file", side_effect=change_after_backup), self.assertRaises(SyncError):
            apply_plans(plans)
        self.assertEqual(entry.read_bytes(), b"new external edit")
        self.assertFalse((home / "skills").exists())

    def test_existing_and_late_locks_are_never_removed(self):
        plans = self.plans()
        lock = self.home() / ".agent-kit/sync.lock"
        lock.parent.mkdir(parents=True)
        lock.write_bytes(b"another process")
        with self.assertRaises(SyncError):
            apply_plans(plans)
        self.assertTrue(self.plans()[0].conflicts)
        self.assertEqual(lock.read_bytes(), b"another process")
        self.assertFalse((self.home() / "AGENTS.md").exists())

    def test_matching_new_skill_is_adopted_and_local_edits_preserved(self):
        self.plans(apply=True)
        source = self.repo / "core/skills/demo/SKILL.md"
        destination = self.home() / "skills/demo/SKILL.md"
        destination.write_bytes(b"local edit")
        self.assertEqual(next(item for item in self.plans()[0].skills if item.rel.endswith("SKILL.md")).action, "preserve")
        self.plans(apply=True)
        self.assertEqual(destination.read_bytes(), b"local edit")
        source.write_bytes(b"local edit")
        plans = self.plans()
        self.assertFalse(plans[0].conflicts)
        self.assertEqual(next(item for item in plans[0].skills if item.rel.endswith("SKILL.md")).action, "adopt")
        apply_plans(plans)
        self.assertFalse(self.plans()[0].has_changes)

    def test_noop_apply_does_not_write_or_back_up(self):
        self.plans(apply=True)
        home = self.home()
        files = {path: (path.read_bytes(), path.stat().st_mtime_ns) for path in home.rglob("*") if path.is_file()}
        plans = self.plans(apply=True)
        self.assertFalse(plans[0].has_changes)
        self.assertEqual(files, {path: (path.read_bytes(), path.stat().st_mtime_ns) for path in home.rglob("*") if path.is_file()})
        self.assertFalse((home / ".agent-kit/backups").exists())

    def test_auto_selects_only_existing_homes(self):
        self.home("claude").mkdir()
        plans = self.plans(target="auto", apply=True)
        self.assertEqual([plan.name for plan in plans], ["claude"])
        self.assertFalse(self.home().exists())
        self.assertFalse(self.home("codex").exists())
        self.assertTrue((self.home("claude") / "CLAUDE.md").exists())

    def test_runtime_config_and_ignored_sources_are_untouched(self):
        home = self.home()
        originals = {}
        for relative in ("cli/config.json", "settings.json", "plugins/private", "skills/demo/user.md"):
            path = home / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b"private")
            originals[path] = b"private"
        root = self.repo / "core/skills/demo"
        for relative in ("SKILL.md.zh.md", ".DS_Store", "__pycache__/helper.pyc", "references/guide.md.zh.md"):
            path = root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b"excluded")
        adapters = {self.repo / rel: (self.repo / rel).read_bytes() for rel, _ in TARGETS.values()}
        self.plans(apply=True)
        for path, content in (originals | adapters).items():
            self.assertEqual(path.read_bytes(), content)
        installed = {path.relative_to(home / "skills").as_posix() for path in (home / "skills").rglob("*") if path.is_file()}
        self.assertEqual(installed, {"demo/SKILL.md", "demo/references/guide.md", "demo/user.md"})

    def test_overlapping_homes_and_non_directory_parents_are_conflicts(self):
        plans = self.plans(target="all", codex_home=self.home(), claude_home=self.home() / "nested")
        self.assertTrue(any("overlap" in item for plan in plans for item in plan.conflicts))
        with self.assertRaises(SyncError):
            apply_plans(plans)
        self.assertFalse(self.home().exists())
        self.home().write_bytes(b"file, not directory")
        self.assertTrue(self.plans()[0].conflicts)
        self.assertTrue(self.plans(target="auto")[0].conflicts)

    def test_link_paths_are_rejected_including_dangling_links(self):
        home = self.home()
        home.mkdir()
        entry = home / "AGENTS.md"
        try:
            entry.symlink_to(self.root / "missing")
        except OSError as exc:
            self.skipTest(f"Symlink creation unavailable: {exc}")
        self.assertTrue(self.plans(replace=["zcode:AGENTS.md"])[0].conflicts)
        self.assertFalse((self.root / "missing").exists())
        self.assertTrue(entry.is_symlink())

    @unittest.skipUnless(os.name == "nt", "Windows junction test")
    def test_windows_junction_ancestor_is_rejected(self):
        import subprocess
        outside = self.root / "outside"
        outside.mkdir()
        link = self.root / "junction"
        result = subprocess.run(["cmd", "/c", "mklink", "/J", str(link), str(outside)], capture_output=True)
        if result.returncode:
            self.skipTest("Cannot create a temporary junction")
        self.addCleanup(lambda: link.rmdir() if link.is_junction() else None)
        plans = self.plans(zcode_home=link / "host")
        self.assertTrue(any("reparse" in item for item in plans[0].conflicts))
        self.assertEqual(list(outside.iterdir()), [])


class TestParseArgs(unittest.TestCase):
    def test_defaults_to_auto_preview(self):
        args = parse_args([])
        self.assertEqual(args.target, "auto")
        self.assertFalse(args.apply)
        self.assertFalse(args.pull)

    def test_named_target_and_apply(self):
        args = parse_args(["--target", "zcode", "--apply", "--pull"])
        self.assertEqual(args.target, "zcode")
        self.assertTrue(args.apply)
        self.assertTrue(args.pull)


if __name__ == "__main__":
    unittest.main(buffer=True)


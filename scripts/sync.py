#!/usr/bin/env python3
"""Sync agent-kit core instructions and skills into agent host homes.

Dual-target distribution: renders core/INSTRUCTIONS.md into the adapter entry
files' marker blocks, then atomically installs adapters and skills into the
Claude Code and Codex home directories.

Zero third-party dependencies. Inline unittest: python scripts/sync.py test
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


CORE_START = "<!-- AGENT-KIT:CORE:START -->"
CORE_END = "<!-- AGENT-KIT:CORE:END -->"
IGNORED_COPY_PATTERNS = shutil.ignore_patterns(".DS_Store", "__pycache__", "*.pyc")


class SyncError(RuntimeError):
    """Raised when the sync cannot complete safely."""


# ---------------------------------------------------------------------------
# Marker-block rendering
# ---------------------------------------------------------------------------


def render_core_block(adapter_text: str, core_text: str) -> str:
    """Render core_text into adapter_text's marker block.

    Content outside the block is preserved. When the block is missing, it is
    appended at the end of the adapter text.
    """
    block = f"{CORE_START}\n{core_text.rstrip()}\n{CORE_END}"
    if CORE_START in adapter_text and CORE_END in adapter_text:
        before, rest = adapter_text.split(CORE_START, 1)
        _, after = rest.split(CORE_END, 1)
        return f"{before}{block}{after}"
    if adapter_text.strip():
        return f"{adapter_text.rstrip()}\n\n{block}\n"
    return f"{block}\n"


def extract_core_block(text: str) -> str:
    """Return the content inside the marker block (without the markers)."""
    _, rest = text.split(CORE_START, 1)
    inner, _ = rest.split(CORE_END, 1)
    return inner.strip()


# ---------------------------------------------------------------------------
# Atomic replace
# ---------------------------------------------------------------------------


def remove_existing(path: Path) -> None:
    if path.is_symlink() or path.is_file():
        path.unlink()
        return
    if path.is_dir():
        shutil.rmtree(path)
        return
    if path.exists():
        raise SyncError(f"Refusing to remove unsupported path type: {path}")


def replace_file(source: Path, target: Path, *, dry_run: bool = False) -> None:
    if not source.is_file():
        raise SyncError(f"Missing source file: {source}")
    if target.exists() and target.is_dir() and not target.is_symlink():
        raise SyncError(f"Refusing to replace directory with file: {target}")
    if dry_run:
        return

    target.parent.mkdir(parents=True, exist_ok=True)
    tmp_target = target.with_name(f".{target.name}.tmp-{os.getpid()}")
    remove_existing(tmp_target)
    try:
        shutil.copy2(source, tmp_target)
        os.replace(tmp_target, target)
    finally:
        remove_existing(tmp_target)


def replace_directory(source: Path, target: Path, *, dry_run: bool = False) -> None:
    if not source.is_dir():
        raise SyncError(f"Missing source directory: {source}")
    if dry_run:
        return

    target.parent.mkdir(parents=True, exist_ok=True)
    tmp_target = target.with_name(f".{target.name}.tmp-{os.getpid()}")
    remove_existing(tmp_target)
    try:
        shutil.copytree(
            source,
            tmp_target,
            symlinks=True,
            ignore=IGNORED_COPY_PATTERNS,
        )
        remove_existing(target)
        tmp_target.rename(target)
    finally:
        remove_existing(tmp_target)


# ---------------------------------------------------------------------------
# Sync orchestration
# ---------------------------------------------------------------------------


def run_git(repo: Path, args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=repo,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def print_process_output(result: subprocess.CompletedProcess[str]) -> None:
    if result.stdout:
        sys.stdout.write(result.stdout)
    if result.stderr:
        sys.stderr.write(result.stderr)


def git_head(repo: Path) -> str:
    result = run_git(repo, ["rev-parse", "HEAD"])
    if result.returncode != 0:
        print_process_output(result)
        raise SyncError("Could not read the current git HEAD.")
    return result.stdout.strip()


def pull_repository(repo: Path) -> bool:
    """Fast-forward pull. Returns True when HEAD moved."""
    before = git_head(repo)
    result = run_git(repo, ["pull", "--ff-only"])
    print_process_output(result)
    if result.returncode != 0:
        raise SyncError("git pull failed; nothing was synced.")
    return before != git_head(repo)


def iter_skill_sources(skills_dir: Path) -> list[Path]:
    if not skills_dir.is_dir():
        raise SyncError(f"Missing source skills directory: {skills_dir}")
    return sorted(
        child
        for child in skills_dir.iterdir()
        if not child.name.startswith(".") and child.is_dir()
    )


# Per-target layout: (adapter entry file inside the repo, entry file name in the host home)
TARGETS = {
    "codex": ("adapters/codex/AGENTS.md", "AGENTS.md"),
    "claude": ("adapters/claude/CLAUDE.md", "CLAUDE.md"),
}


def sync_target(repo: Path, target: str, home: Path, *, dry_run: bool = False) -> list[str]:
    """Render core into the adapter entry, then install entry + skills into home."""
    adapter_rel, entry_name = TARGETS[target]
    adapter_path = repo / adapter_rel
    core_path = repo / "core" / "INSTRUCTIONS.md"
    if not adapter_path.is_file():
        raise SyncError(f"Missing adapter entry file: {adapter_path}")
    if not core_path.is_file():
        raise SyncError(f"Missing core instructions file: {core_path}")

    core_text = core_path.read_text(encoding="utf-8")
    rendered = render_core_block(adapter_path.read_text(encoding="utf-8"), core_text)
    if not dry_run:
        adapter_path.write_text(rendered, encoding="utf-8")

    replace_file(adapter_path, home / entry_name, dry_run=dry_run)
    synced = [entry_name]

    for skill_dir in iter_skill_sources(repo / "core" / "skills"):
        replace_directory(skill_dir, home / "skills" / skill_dir.name, dry_run=dry_run)
        synced.append(f"skills/{skill_dir.name}")
    return synced


def sync_all(
    repo: Path,
    *,
    codex_home: Path | None = None,
    claude_home: Path | None = None,
    dry_run: bool = False,
    target: str = "all",
) -> dict[str, list[str]]:
    repo = repo.resolve()
    results: dict[str, list[str]] = {}
    wanted = list(TARGETS) if target == "all" else [target]
    homes = {"codex": codex_home, "claude": claude_home}
    for name in wanted:
        home = homes[name]
        if home is None:
            raise SyncError(f"No home directory configured for target: {name}")
        results[name] = sync_target(repo, name, home.expanduser(), dry_run=dry_run)
    return results


def deploy_after_pull(
    repo: Path,
    *,
    codex_home: Path,
    claude_home: Path,
    force: bool = False,
    dry_run: bool = False,
    target: str = "all",
) -> bool:
    if dry_run:
        # A preview must never be blocked by (or depend on) a git pull.
        print("Dry run: skipping git pull; nothing will be written.")
    else:
        try:
            did_update = pull_repository(repo)
        except SyncError as exc:
            if not force:
                raise
            print(f"git pull did not complete ({exc}); syncing because --force was set.")
        else:
            if not did_update and not force:
                print("No git updates found; exiting without syncing.")
                return False
            if force:
                print("Syncing after git pull because --force was set.")

    results = sync_all(
        repo,
        codex_home=codex_home,
        claude_home=claude_home,
        dry_run=dry_run,
        target=target,
    )
    for name, synced in results.items():
        home = {"codex": codex_home, "claude": claude_home}[name].expanduser()
        prefix = "Would sync" if dry_run else "Synced"
        print(f"{prefix} {len(synced)} item(s) into {home} (target: {name}):")
        for item in synced:
            print(f"  - {item}")
    return True


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Render core/INSTRUCTIONS.md into adapter entries and sync them plus "
            "core/skills/* into the Claude Code and Codex home directories."
        )
    )
    parser.add_argument(
        "--target",
        choices=["codex", "claude", "all"],
        default="all",
        help="Which agent host to sync. Defaults to all.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would be synced without writing anything.",
    )
    parser.add_argument(
        "-f",
        "--force",
        action="store_true",
        help="Sync even when git pull found no update or failed.",
    )
    parser.add_argument(
        "--repo",
        type=Path,
        default=Path(__file__).resolve().parent.parent,
        help="agent-kit repository root. Defaults to the parent of this script.",
    )
    parser.add_argument(
        "--codex-home",
        type=Path,
        default=Path.home() / ".codex",
        help="Destination Codex home. Defaults to ~/.codex.",
    )
    parser.add_argument(
        "--claude-home",
        type=Path,
        default=Path.home() / ".claude",
        help="Destination Claude Code home. Defaults to ~/.claude.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]
    if argv == ["test"]:
        unittest.main(module=None, argv=[sys.argv[0], "-v"], exit=False)
        return 0
    args = parse_args(argv)
    try:
        deploy_after_pull(
            args.repo,
            codex_home=args.codex_home,
            claude_home=args.claude_home,
            force=args.force,
            dry_run=args.dry_run,
            target=args.target,
        )
    except SyncError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


# ---------------------------------------------------------------------------
# Inline tests
# ---------------------------------------------------------------------------


class TestRenderCoreBlock(unittest.TestCase):
    def test_renders_core_into_marker_block(self):
        adapter = "# Entry\n\n<!-- AGENT-KIT:CORE:START -->\nold\n<!-- AGENT-KIT:CORE:END -->\n\nTail\n"
        result = render_core_block(adapter, "NEW CORE")
        self.assertIn("<!-- AGENT-KIT:CORE:START -->", result)
        self.assertIn("NEW CORE", result)
        self.assertNotIn("old", result)
        self.assertTrue(result.startswith("# Entry"))
        self.assertTrue(result.endswith("Tail\n"))

    def test_creates_marker_block_when_missing(self):
        adapter = "# Entry only\n"
        result = render_core_block(adapter, "CORE")
        self.assertIn("<!-- AGENT-KIT:CORE:START -->\nCORE\n<!-- AGENT-KIT:CORE:END -->", result)

    def test_preserves_content_outside_block(self):
        adapter = "Head\n\n<!-- AGENT-KIT:CORE:START -->\nx\n<!-- AGENT-KIT:CORE:END -->\n\nTail"
        result = render_core_block(adapter, "y")
        self.assertEqual(
            result,
            "Head\n\n<!-- AGENT-KIT:CORE:START -->\ny\n<!-- AGENT-KIT:CORE:END -->\n\nTail",
        )

    def test_empty_adapter_gets_block_only(self):
        result = render_core_block("", "CORE")
        self.assertTrue(result.startswith("<!-- AGENT-KIT:CORE:START -->"))
        self.assertIn("CORE", result)

    def test_extract_core_block_roundtrip(self):
        adapter = "Head\n\n<!-- AGENT-KIT:CORE:START -->\nold\n<!-- AGENT-KIT:CORE:END -->\n\nTail"
        rendered = render_core_block(adapter, "  round trip  ")
        self.assertEqual(extract_core_block(rendered), "round trip")


class TestReplaceFile(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.dir = Path(self.tmp.name)

    def test_replace_file_atomic_write(self):
        src = self.dir / "src.md"
        src.write_text("content", encoding="utf-8")
        dst = self.dir / "sub" / "dst.md"
        replace_file(src, dst)
        self.assertEqual(dst.read_text(encoding="utf-8"), "content")

    def test_replace_file_refuses_directory(self):
        src = self.dir / "src.md"
        src.write_text("content", encoding="utf-8")
        dst = self.dir / "adir"
        dst.mkdir()
        with self.assertRaises(SyncError):
            replace_file(src, dst)

    def test_dry_run_touches_nothing(self):
        src = self.dir / "src.md"
        src.write_text("content", encoding="utf-8")
        dst = self.dir / "dst.md"
        replace_file(src, dst, dry_run=True)
        self.assertFalse(dst.exists())


class TestSyncTargets(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo = Path(self.tmp.name) / "repo"
        (self.repo / "core" / "skills" / "demo").mkdir(parents=True)
        (self.repo / "core" / "skills" / "demo" / "SKILL.md").write_text("x", encoding="utf-8")
        (self.repo / "core" / "INSTRUCTIONS.md").write_text("CORE", encoding="utf-8")
        codex_dir = self.repo / "adapters" / "codex"
        codex_dir.mkdir(parents=True)
        (codex_dir / "AGENTS.md").write_text(
            "# Codex\n\n<!-- AGENT-KIT:CORE:START -->\nold\n<!-- AGENT-KIT:CORE:END -->\n",
            encoding="utf-8",
        )
        claude_dir = self.repo / "adapters" / "claude"
        claude_dir.mkdir(parents=True)
        (claude_dir / "CLAUDE.md").write_text(
            "# Claude\n\n<!-- AGENT-KIT:CORE:START -->\nold\n<!-- AGENT-KIT:CORE:END -->\n",
            encoding="utf-8",
        )

    def test_sync_codex_target_only(self):
        home = Path(self.tmp.name) / "codex-home"
        claude_home = Path(self.tmp.name) / "claude-home"
        results = sync_all(
            self.repo,
            codex_home=home,
            claude_home=claude_home,
            dry_run=False,
            target="codex",
        )
        self.assertIn("AGENTS.md", results["codex"])
        self.assertTrue((home / "AGENTS.md").exists())
        self.assertTrue((home / "skills" / "demo" / "SKILL.md").exists())
        self.assertIn("Codex", (home / "AGENTS.md").read_text(encoding="utf-8"))
        self.assertIn("CORE", (home / "AGENTS.md").read_text(encoding="utf-8"))
        # claude target untouched
        self.assertFalse(claude_home.exists())

    def test_sync_all_targets(self):
        codex_home = Path(self.tmp.name) / "c1"
        claude_home = Path(self.tmp.name) / "c2"
        sync_all(self.repo, codex_home=codex_home, claude_home=claude_home, dry_run=False)
        self.assertTrue((codex_home / "AGENTS.md").exists())
        self.assertTrue((claude_home / "CLAUDE.md").exists())
        # adapter files in repo were updated with rendered core
        self.assertEqual(
            extract_core_block((self.repo / "adapters" / "codex" / "AGENTS.md").read_text(encoding="utf-8")),
            "CORE",
        )

    def test_dry_run_touches_nothing(self):
        home = Path(self.tmp.name) / "never"
        sync_all(self.repo, codex_home=home, claude_home=home, dry_run=True)
        self.assertFalse(home.exists())
        # adapter files in repo also untouched under dry-run
        self.assertEqual(
            extract_core_block((self.repo / "adapters" / "codex" / "AGENTS.md").read_text(encoding="utf-8")),
            "old",
        )

    def test_sync_claude_target_only(self):
        codex_home = Path(self.tmp.name) / "never-codex"
        claude_home = Path(self.tmp.name) / "claude-home"
        results = sync_all(
            self.repo,
            codex_home=codex_home,
            claude_home=claude_home,
            dry_run=False,
            target="claude",
        )
        self.assertIn("CLAUDE.md", results["claude"])
        self.assertTrue((claude_home / "CLAUDE.md").exists())
        self.assertTrue((claude_home / "skills" / "demo" / "SKILL.md").exists())
        # codex target untouched
        self.assertFalse(codex_home.exists())


class TestDeployAfterPullDryRun(unittest.TestCase):
    """Regression: --dry-run must not be blocked by the git-pull gate.

    The sync_all-level tests bypass deploy_after_pull entirely; these cases
    exercise the CLI gate layer against a repo that has no git remote at all.
    """

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo = Path(self.tmp.name) / "repo"
        (self.repo / "core" / "skills" / "demo").mkdir(parents=True)
        (self.repo / "core" / "skills" / "demo" / "SKILL.md").write_text("x", encoding="utf-8")
        (self.repo / "core" / "INSTRUCTIONS.md").write_text("CORE", encoding="utf-8")
        codex_dir = self.repo / "adapters" / "codex"
        codex_dir.mkdir(parents=True)
        (codex_dir / "AGENTS.md").write_text(
            "# Codex\n\n<!-- AGENT-KIT:CORE:START -->\nold\n<!-- AGENT-KIT:CORE:END -->\n",
            encoding="utf-8",
        )
        claude_dir = self.repo / "adapters" / "claude"
        claude_dir.mkdir(parents=True)
        (claude_dir / "CLAUDE.md").write_text(
            "# Claude\n\n<!-- AGENT-KIT:CORE:START -->\nold\n<!-- AGENT-KIT:CORE:END -->\n",
            encoding="utf-8",
        )

    def test_dry_run_works_without_git_remote(self):
        home = Path(self.tmp.name) / "home"
        # No git repo at all: pull would raise, dry-run must still preview.
        deployed = deploy_after_pull(
            self.repo,
            codex_home=home,
            claude_home=home,
            dry_run=True,
        )
        self.assertTrue(deployed)
        self.assertFalse(home.exists())
        self.assertEqual(
            extract_core_block((self.repo / "adapters" / "codex" / "AGENTS.md").read_text(encoding="utf-8")),
            "old",
        )


def _load_tests(loader: unittest.TestLoader, tests: list, pattern: str):
    suite = unittest.TestSuite()
    for cls in (TestRenderCoreBlock, TestReplaceFile, TestSyncTargets, TestDeployAfterPullDryRun):
        suite.addTests(loader.loadTestsFromTestCase(cls))
    return suite


if __name__ == "__main__":
    if len(sys.argv) >= 2 and sys.argv[1] == "test":
        unittest.main(argv=[sys.argv[0]], exit=False)
    else:
        raise SystemExit(main(sys.argv[1:]))

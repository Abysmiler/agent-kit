#!/usr/bin/env python3
from __future__ import annotations

import argparse
import errno
import hashlib
import json
import os
import re
import stat
import subprocess
import sys
import tempfile
import unittest
import uuid
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path


CORE_START = "<!-- AGENT-KIT:CORE:START -->"
CORE_END = "<!-- AGENT-KIT:CORE:END -->"
MANIFEST_DIR = ".agent-kit"
MANIFEST_NAME = "manifest.json"
MANIFEST_VERSION = 1
WRITE_ACTIONS = {"create", "update", "replace", "state-update"}
TARGETS = {
    "codex": ("adapters/codex/AGENTS.md", "AGENTS.md"),
    "claude": ("adapters/claude/CLAUDE.md", "CLAUDE.md"),
    "zcode": ("adapters/zcode/AGENTS.md", "AGENTS.md"),
}


class SyncError(RuntimeError):
    pass


@dataclass(frozen=True)
class Snapshot:
    content: bytes | None = None
    mode: int | None = None


@dataclass
class FilePlan:
    rel: str
    action: str
    destination: Path
    snapshot: Snapshot
    content: bytes | None = None
    mode: int | None = None
    detail: str = ""

    @property
    def writes(self) -> bool:
        return self.action in WRITE_ACTIONS

    @property
    def backup(self) -> bool:
        return self.writes and self.snapshot.content is not None


@dataclass
class TargetPlan:
    name: str
    home: Path
    entry: FilePlan | None = None
    skills: list[FilePlan] = field(default_factory=list)
    manifest: FilePlan | None = None
    conflicts: list[str] = field(default_factory=list)
    stale: list[str] = field(default_factory=list)
    inputs: dict[Path, Snapshot] = field(default_factory=dict)
    skills_root: Path | None = None
    skill_sources: set[Path] = field(default_factory=set)
    backup_root: Path | None = None

    @property
    def actions(self) -> list[FilePlan]:
        return ([self.entry] if self.entry else []) + self.skills + ([self.manifest] if self.manifest else [])

    @property
    def has_changes(self) -> bool:
        return any(action.writes for action in self.actions)


def marker_state(text: str) -> str:
    starts, ends = text.count(CORE_START), text.count(CORE_END)
    if starts == 0 and ends == 0:
        return "malformed" if "AGENT-KIT:CORE" in text else "missing"
    if starts != 1 or ends != 1 or text.count("AGENT-KIT:CORE") != 2 or text.index(CORE_START) >= text.index(CORE_END):
        return "malformed"
    return "valid"


def normalized_text(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n").strip()


def render_core_block(adapter_text: str, core_text: str) -> str:
    block = f"{CORE_START}\n{normalized_text(core_text)}\n{CORE_END}"
    state = marker_state(adapter_text)
    if state == "valid":
        before, rest = adapter_text.split(CORE_START, 1)
        inner, after = rest.split(CORE_END, 1)
        if inner.startswith("\r\n"):
            block = block.replace("\n", "\r\n")
        return f"{before}{block}{after}"
    if state == "malformed":
        raise SyncError("Cannot render an adapter with malformed or duplicate core markers.")
    if adapter_text.strip():
        return f"{adapter_text.rstrip()}\n\n{block}\n"
    return f"{block}\n"


def extract_core_block(text: str) -> str:
    if marker_state(text) != "valid":
        raise SyncError("Core marker block is missing or malformed.")
    return text.split(CORE_START, 1)[1].split(CORE_END, 1)[0].strip()


def sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def sha256_text(content: str) -> str:
    return sha256_bytes(normalized_text(content).encode("utf-8"))


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def path_stat(path: Path):
    try:
        result = path.lstat()
    except FileNotFoundError:
        return None
    if stat.S_ISLNK(result.st_mode) or getattr(result, "st_file_attributes", 0) & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400):
        raise SyncError(f"Symlinks, junctions and reparse points are not supported: {path}")
    return result


def check_directory(path: Path) -> None:
    for part in (path, *path.parents):
        result = path_stat(part)
        if result is not None and not stat.S_ISDIR(result.st_mode):
            raise SyncError(f"Path is not a directory: {part}")


def read_snapshot(path: Path) -> Snapshot:
    check_directory(path.parent)
    before = path_stat(path)
    if before is None:
        return Snapshot()
    if not stat.S_ISREG(before.st_mode):
        raise SyncError(f"Path is not a regular file: {path}")
    content = path.read_bytes()
    after = path_stat(path)
    if after is None or (before.st_ino, before.st_size, before.st_mtime_ns, before.st_mode) != (after.st_ino, after.st_size, after.st_mtime_ns, after.st_mode):
        raise SyncError(f"File changed while reading; rerun sync: {path}")
    return Snapshot(content, stat.S_IMODE(after.st_mode))


def verify_snapshot(path: Path, expected: Snapshot) -> None:
    if read_snapshot(path) != expected:
        raise SyncError(f"File changed after planning; rerun sync: {path}")


def valid_relative_path(value: str) -> bool:
    if not isinstance(value, str) or not value or any(ord(char) < 32 or char in '\\<>:"|?*' for char in value):
        return False
    reserved = {"CON", "PRN", "AUX", "NUL", *(f"COM{i}" for i in range(1, 10)), *(f"LPT{i}" for i in range(1, 10))}
    return all(part not in {"", ".", ".."} and part == part.rstrip(" .") and part.split(".")[0].upper() not in reserved for part in value.split("/"))


def is_ignored_source(path: Path) -> bool:
    return path.name == ".DS_Store" or path.name.endswith(".zh.md") or path.suffix == ".pyc" or "__pycache__" in path.parts


def iter_skill_sources(skills_dir: Path) -> list[Path]:
    check_directory(skills_dir)
    if not skills_dir.is_dir():
        raise SyncError(f"Missing source skills directory: {skills_dir}")
    files: list[Path] = []

    def visit(directory: Path) -> None:
        for path in sorted(directory.iterdir()):
            if is_ignored_source(path):
                continue
            info = path_stat(path)
            if info is None:
                raise SyncError(f"Source disappeared during planning: {path}")
            if stat.S_ISDIR(info.st_mode):
                visit(path)
            elif stat.S_ISREG(info.st_mode):
                relative = path.relative_to(skills_dir).as_posix()
                if not valid_relative_path(relative):
                    raise SyncError(f"Unsafe source path: {path}")
                files.append(path)
            else:
                raise SyncError(f"Source is not a regular file or directory: {path}")

    for skill_dir in sorted(skills_dir.iterdir()):
        if skill_dir.name.startswith(".") or is_ignored_source(skill_dir):
            continue
        info = path_stat(skill_dir)
        if info is None:
            raise SyncError(f"Source disappeared during planning: {skill_dir}")
        if stat.S_ISDIR(info.st_mode):
            visit(skill_dir)
    aliases: dict[str, Path] = {}
    for path in files:
        relative = path.relative_to(skills_dir).as_posix()
        alias = os.path.normcase(relative)
        if alias in aliases:
            raise SyncError(f"Skill source paths collide on this platform: {aliases[alias]} and {path}")
        aliases[alias] = path
    return files


def manifest_path(home: Path) -> Path:
    return home / MANIFEST_DIR / MANIFEST_NAME


def unique_object(pairs: list[tuple]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise SyncError(f"Duplicate manifest key: {key}")
        result[key] = value
    return result


def load_manifest(content: bytes | None, target: str) -> dict:
    if content is None:
        return {}
    try:
        data = json.loads(content.decode("utf-8"), object_pairs_hook=unique_object)
    except (UnicodeError, ValueError) as exc:
        raise SyncError(f"Cannot decode manifest: {exc}") from exc
    if not isinstance(data, dict) or set(data) != {"version", "target", "entry", "skills"}:
        raise SyncError("Malformed manifest fields; resolve the manifest manually.")
    if type(data["version"]) is not int or data["version"] != MANIFEST_VERSION or data["target"] != target:
        raise SyncError("Unsupported manifest version or target mismatch.")
    entry, skills = data["entry"], data["skills"]
    is_hash = lambda value: isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value) is not None
    if not isinstance(entry, dict) or set(entry) != {"path", "core_sha256"} or entry["path"] != TARGETS[target][1] or not is_hash(entry["core_sha256"]):
        raise SyncError("Malformed entry baseline in manifest.")
    if not isinstance(skills, dict) or any(not valid_relative_path(key) or "/" not in key or not is_hash(value) for key, value in skills.items()):
        raise SyncError("Unsafe skill paths or malformed hashes in manifest.")
    aliases: set[str] = set()
    for key in skills:
        alias = os.path.normcase(key)
        if alias in aliases:
            raise SyncError(f"Aliased skill paths in manifest: {key}")
        aliases.add(alias)
    return data


def manifest_bytes(data: dict) -> bytes:
    return (json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def plan_entry(plan: TargetPlan, entry_name: str, rendered: str, core: str, previous_hash: str | None, replace: set[str]) -> FilePlan:
    destination = plan.home / entry_name
    snapshot = read_snapshot(destination)
    desired = rendered.encode("utf-8")
    if snapshot.content is None:
        return FilePlan(entry_name, "create", destination, snapshot, desired, detail="entry does not exist")
    try:
        existing = snapshot.content.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise SyncError(f"Cannot inspect entry markers safely; convert the entry to UTF-8 before syncing: {destination}") from exc
    if "\x00" in existing:
        raise SyncError(f"Entry contains NUL bytes; check its encoding before syncing: {destination}")
    state = marker_state(existing)
    if state == "malformed":
        raise SyncError(f"Entry has malformed or duplicate core markers: {destination}")
    if state == "missing":
        return FilePlan(entry_name, "replace", destination, snapshot, desired, snapshot.mode, "verified backup then replace; old rules will no longer be active")
    current_hash, desired_hash = sha256_text(extract_core_block(existing)), sha256_text(core)
    if current_hash == desired_hash:
        return FilePlan(entry_name, "skip" if previous_hash == desired_hash else "adopt", destination, snapshot, detail="core already matches; preserve all existing bytes")
    if current_hash != previous_hash and entry_name not in replace:
        raise SyncError(f"Core block has no matching baseline or was locally edited: {destination}; review and use --replace {plan.name}:{entry_name} to replace only the block")
    candidate = render_core_block(existing, core).encode("utf-8")
    return FilePlan(entry_name, "replace" if entry_name in replace else "update", destination, snapshot, candidate, snapshot.mode, "replace core block only; preserve outside bytes")


def plan_skill(plan: TargetPlan, source: Path, previous: dict[str, str], replace: set[str]) -> tuple[FilePlan, str | None]:
    relative = source.relative_to(plan.skills_root).as_posix()
    rel = f"skills/{relative}"
    destination = plan.home / rel
    snapshot = read_snapshot(destination)
    source_snapshot = read_snapshot(source)
    if source_snapshot.content is None:
        raise SyncError(f"Missing source skill file: {source}")
    plan.inputs[source] = source_snapshot
    source_hash = sha256_bytes(source_snapshot.content)
    previous_hash = previous.get(relative)
    current_hash = sha256_bytes(snapshot.content) if snapshot.content is not None else None
    action, detail, baseline = "skip", "already current", source_hash
    if current_hash == source_hash:
        action = "skip" if previous_hash == source_hash else "adopt"
    elif rel in replace:
        action, detail = ("replace" if current_hash is not None else "create"), "file-scoped replacement authorized"
    elif current_hash is None and previous_hash is None:
        action, detail = "create", "new skill file"
    elif previous_hash is not None and current_hash != previous_hash:
        if source_hash != previous_hash:
            raise SyncError(f"User changed/deleted skill and source also changed: {destination}; review and use --replace {plan.name}:{rel}")
        action, detail, baseline = "preserve", "user changed/deleted file; source is unchanged", previous_hash
    elif previous_hash is None:
        raise SyncError(f"Unmanaged skill file differs from source: {destination}; review and use --replace {plan.name}:{rel}")
    else:
        action, detail = "update", "source changed; local file matches baseline"
    mode = snapshot.mode if snapshot.content is not None else source_snapshot.mode
    return FilePlan(rel, action, destination, snapshot, source_snapshot.content, mode, detail), baseline


def plan_target(repo: Path, target: str, home: Path, replace: set[str] | None = None) -> TargetPlan:
    plan = TargetPlan(target, home)
    replace = replace or set()
    adapter_rel, entry_name = TARGETS[target]
    try:
        check_directory(home)
        check_directory(home / MANIFEST_DIR / "backups")
        if path_stat(home / MANIFEST_DIR / "sync.lock") is not None:
            raise SyncError(f"Sync lock exists; investigate the running process or stale lock: {home / MANIFEST_DIR / 'sync.lock'}")
        state_snapshot = read_snapshot(manifest_path(home))
        state = load_manifest(state_snapshot.content, target)
        core_path, adapter_path = repo / "core/INSTRUCTIONS.md", repo / adapter_rel
        for path in (core_path, adapter_path):
            snapshot = read_snapshot(path)
            if snapshot.content is None:
                raise SyncError(f"Missing source instructions: {path}")
            plan.inputs[path] = snapshot
        core = plan.inputs[core_path].content.decode("utf-8")
        if "AGENT-KIT:CORE" in core:
            raise SyncError("Core source must not contain managed-block markers.")
        rendered = render_core_block(plan.inputs[adapter_path].content.decode("utf-8"), core)
        plan.skills_root = repo / "core/skills"
        plan.skill_sources = set(iter_skill_sources(plan.skills_root))
    except (OSError, UnicodeError, SyncError) as exc:
        plan.conflicts.append(str(exc))
        return plan
    try:
        plan.entry = plan_entry(plan, entry_name, rendered, core, state.get("entry", {}).get("core_sha256"), replace)
    except (OSError, UnicodeError, SyncError) as exc:
        plan.conflicts.append(f"{entry_name}: {exc}")
    previous = state.get("skills", {})
    new_skills = dict(previous)
    known_paths = {entry_name}
    source_relatives = set()
    for source in sorted(plan.skill_sources):
        relative = source.relative_to(plan.skills_root).as_posix()
        source_relatives.add(relative)
        known_paths.add(f"skills/{relative}")
        try:
            action, baseline = plan_skill(plan, source, previous, replace)
            plan.skills.append(action)
            new_skills[relative] = baseline
        except (OSError, SyncError) as exc:
            plan.conflicts.append(str(exc))
    for relative in sorted(previous.keys() - source_relatives):
        rel, destination = f"skills/{relative}", home / "skills" / relative
        plan.stale.append(rel)
        try:
            plan.skills.append(FilePlan(rel, "stale", destination, read_snapshot(destination), detail="removed from source; local presence/absence and baseline preserved"))
        except (OSError, SyncError) as exc:
            plan.conflicts.append(str(exc))
    for rel in sorted(replace - known_paths):
        plan.conflicts.append(f"Replacement is not a current source file or entry: {target}:{rel}")
    state_content = manifest_bytes({
        "version": MANIFEST_VERSION,
        "target": target,
        "entry": {"path": entry_name, "core_sha256": sha256_text(core)},
        "skills": new_skills,
    })
    try:
        load_manifest(state_content, target)
    except SyncError as exc:
        plan.conflicts.append(str(exc))
    action = "skip" if state_snapshot.content == state_content else "create" if state_snapshot.content is None else "state-update"
    plan.manifest = FilePlan(f"{MANIFEST_DIR}/{MANIFEST_NAME}", action, manifest_path(home), state_snapshot, state_content, state_snapshot.mode if state_snapshot.mode is not None else 0o600, "record managed hashes")
    return plan


def resolve_target_names(target: str, homes: dict[str, Path]) -> list[str]:
    if target == "all":
        return list(TARGETS)
    if target == "auto":
        return [name for name in TARGETS if os.path.lexists(homes[name].expanduser())]
    if target not in TARGETS:
        raise SyncError(f"Unknown target: {target}")
    return [target]


def parse_replacements(values: list[str] | tuple[str, ...], names: list[str]) -> dict[str, set[str]]:
    result = {name: set() for name in names}
    for value in values:
        name, separator, relative = value.partition(":")
        if not separator or name not in TARGETS or not valid_relative_path(relative):
            raise SyncError(f"Invalid --replace; use TARGET:RELATIVE_PATH without wildcards: {value}")
        if name not in result:
            raise SyncError(f"--replace target is not selected: {name}")
        if relative != TARGETS[name][1] and not (relative.startswith("skills/") and len(relative.split("/")) >= 3):
            raise SyncError(f"--replace can only name an entry or a source skill file: {value}")
        result[name].add(relative)
    return result


def paths_overlap(first: Path, second: Path) -> bool:
    first, second = first.resolve(), second.resolve()
    return first == second or first in second.parents or second in first.parents


def build_plans(repo: Path, homes: dict[str, Path], target: str, replace: list[str] | tuple[str, ...] = ()) -> list[TargetPlan]:
    repo = repo.expanduser().resolve()
    names = resolve_target_names(target, homes)
    replacements = parse_replacements(replace, names)
    plans = [plan_target(repo, name, Path(os.path.abspath(homes[name].expanduser())), replacements[name]) for name in names]
    for index, plan in enumerate(plans):
        if paths_overlap(plan.home, repo):
            plan.conflicts.append(f"Target home overlaps the source repository: {plan.home}")
        for other in plans[:index]:
            if paths_overlap(plan.home, other.home):
                message = f"Target homes overlap: {other.name}={other.home}, {plan.name}={plan.home}"
                plan.conflicts.append(message)
                other.conflicts.append(message)
    return plans


def print_plans(plans: list[TargetPlan], *, apply: bool) -> None:
    if not plans:
        print("No existing host home detected; nothing will be created. Select --target codex, claude, zcode, or all explicitly to create missing homes.")
        return
    print(f"Sync mode: {'apply' if apply else 'preview'}")
    for plan in plans:
        print(f"[{plan.name}] {plan.home}")
        if plan.entry:
            print(f"  - {plan.entry.action}: {plan.entry.rel} ({plan.entry.detail})")
        counts = Counter(action.action for action in plan.skills)
        if counts:
            print("  - skills: " + ", ".join(f"{name}={counts[name]}" for name in sorted(counts)))
        for action in plan.skills:
            if action.action != "skip":
                print(f"    - {action.action}: {action.rel} ({action.detail})")
        if plan.manifest:
            print(f"  - {plan.manifest.action}: {plan.manifest.rel} ({plan.manifest.detail})")
        for message in plan.conflicts:
            print(f"  - CONFLICT: {message}")
    count = sum(len(plan.conflicts) for plan in plans)
    if count:
        print(f"Sync stopped: {count} conflict(s); no target was modified.")
    elif not apply:
        print("Preview only; no files were modified. Use --apply after reviewing the plan.")
    else:
        print("Preflight complete; all required backups must be verified before configuration writes.")


def create_directories(path: Path, created: list[Path]) -> None:
    check_directory(path)
    if path.is_dir():
        return
    create_directories(path.parent, created)
    try:
        path.mkdir(mode=0o700)
        created.append(path)
    except FileExistsError:
        check_directory(path)


def atomic_write_bytes(target: Path, content: bytes, *, mode: int | None = None, expected: Snapshot | None = None) -> None:
    check_directory(target.parent)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{target.name}.tmp-", dir=target.parent)
    temporary = Path(temporary)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        if mode is not None:
            temporary.chmod(mode)
        if expected is not None:
            verify_snapshot(target, expected)
        else:
            read_snapshot(target)
        os.replace(temporary, target)
    finally:
        if temporary.exists():
            temporary.unlink()


def backup_file(source: Path, backup: Path, expected: Snapshot) -> None:
    verify_snapshot(source, expected)
    with backup.open("xb") as stream:
        stream.write(expected.content)
        stream.flush()
        os.fsync(stream.fileno())
    if expected.mode is not None:
        backup.chmod(expected.mode)
    verify_snapshot(backup, expected)


def prepare_backups(plans: list[TargetPlan], created: list[Path]) -> dict[Path, Path]:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S-%f") + "-" + uuid.uuid4().hex[:12]
    backups: dict[Path, Path] = {}
    for plan in plans:
        for action in plan.actions:
            if not action.backup:
                continue
            if plan.backup_root is None:
                plan.backup_root = plan.home / MANIFEST_DIR / "backups" / stamp
                create_directories(plan.backup_root.parent, created)
                plan.backup_root.mkdir(mode=0o700)
                created.append(plan.backup_root)
            backup = plan.backup_root / action.rel
            create_directories(backup.parent, created)
            backup_file(action.destination, backup, action.snapshot)
            backups[action.destination] = backup
    return backups


def verify_plans(plans: list[TargetPlan]) -> None:
    for plan in plans:
        check_directory(plan.home)
        check_directory(plan.home / MANIFEST_DIR / "backups")
        if plan.skills_root is not None and set(iter_skill_sources(plan.skills_root)) != plan.skill_sources:
            raise SyncError(f"Source skill file list changed after planning: {plan.skills_root}")
        for path, expected in plan.inputs.items():
            verify_snapshot(path, expected)
        for action in plan.actions:
            verify_snapshot(action.destination, action.snapshot)


def rollback(changed: list[FilePlan], backups: dict[Path, Path]) -> list[str]:
    errors = []
    for action in reversed(changed):
        try:
            current = read_snapshot(action.destination)
            if current == action.snapshot:
                continue
            if current.content != action.content:
                raise SyncError("file was changed externally; not overwriting it during rollback")
            if action.snapshot.content is None:
                action.destination.unlink()
            else:
                backup = backups[action.destination]
                verify_snapshot(backup, action.snapshot)
                atomic_write_bytes(action.destination, action.snapshot.content, mode=action.snapshot.mode, expected=current)
                verify_snapshot(action.destination, action.snapshot)
        except (OSError, SyncError, KeyError) as exc:
            errors.append(f"{action.destination}: {exc}")
    return errors


def apply_plans(plans: list[TargetPlan]) -> None:
    if any(plan.conflicts for plan in plans):
        raise SyncError("Conflicts found; no target was modified.")
    if not any(plan.has_changes for plan in plans):
        verify_plans(plans)
        return
    created: list[Path] = []
    locks: list[tuple[Path, bytes]] = []
    changed: list[FilePlan] = []
    backups: dict[Path, Path] = {}
    failure: Exception | None = None
    cleanup_errors: list[str] = []
    try:
        verify_plans(plans)
        for plan in sorted(plans, key=lambda item: str(item.home)):
            lock = plan.home / MANIFEST_DIR / "sync.lock"
            create_directories(lock.parent, created)
            token = f"pid={os.getpid()} batch={uuid.uuid4().hex}\n".encode("ascii")
            descriptor = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            locks.append((lock, token))
            with os.fdopen(descriptor, "wb") as stream:
                stream.write(token)
        verify_plans(plans)
        backups = prepare_backups(plans, created)
        verify_plans(plans)
        for plan in plans:
            for action in plan.actions:
                if action.backup:
                    verify_snapshot(backups[action.destination], action.snapshot)
        ordered = [action for plan in plans for action in ([plan.entry] if plan.entry else []) + plan.skills]
        ordered.extend(plan.manifest for plan in plans if plan.manifest)
        for action in ordered:
            if not action.writes:
                continue
            if action.content is None:
                raise SyncError(f"Missing planned content: {action.rel}")
            create_directories(action.destination.parent, created)
            changed.append(action)
            atomic_write_bytes(action.destination, action.content, mode=action.mode, expected=action.snapshot)
            if read_snapshot(action.destination).content != action.content:
                raise SyncError(f"Write verification failed: {action.destination}")
    except (Exception, KeyboardInterrupt) as exc:
        errors = rollback(changed, backups)
        status = "Rollback incomplete: " + "; ".join(errors) if errors else "Written files were restored." if changed else "No configuration files were written."
        recovery = ", ".join(str(plan.backup_root) for plan in plans if plan.backup_root is not None)
        failure = SyncError(f"Sync failed: {exc}. {status}" + (f" Backups retained at: {recovery}" if recovery else ""))
    finally:
        for lock, token in reversed(locks):
            try:
                if read_snapshot(lock).content != token:
                    raise SyncError("lock contents changed; refusing to remove it")
                lock.unlink()
            except (OSError, SyncError) as exc:
                cleanup_errors.append(f"{lock}: {exc}")
        if failure:
            for directory in reversed(created):
                try:
                    check_directory(directory)
                    directory.rmdir()
                except OSError as exc:
                    if exc.errno not in {errno.ENOENT, errno.ENOTEMPTY, errno.EEXIST}:
                        cleanup_errors.append(f"{directory}: {exc}")
                except SyncError as exc:
                    cleanup_errors.append(str(exc))
    if cleanup_errors:
        raise SyncError(f"{failure or 'Configuration writes completed.'} Lock/directory cleanup needs attention: {'; '.join(cleanup_errors)}")
    if failure:
        raise failure


def run_git(repo: Path, args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], cwd=repo, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)


def print_process_output(result: subprocess.CompletedProcess[str]) -> None:
    if result.stdout:
        sys.stdout.write(result.stdout)
    if result.stderr:
        sys.stderr.write(result.stderr)


def git_head(repo: Path) -> str:
    result = run_git(repo, ["rev-parse", "HEAD"])
    if result.returncode:
        print_process_output(result)
        raise SyncError("Could not read the current git HEAD.")
    return result.stdout.strip()


def pull_repository(repo: Path) -> bool:
    before = git_head(repo)
    result = run_git(repo, ["pull", "--ff-only"])
    print_process_output(result)
    if result.returncode:
        raise SyncError("git pull failed; nothing was synced.")
    return before != git_head(repo)


def sync_all(repo: Path, *, codex_home: Path | None = None, claude_home: Path | None = None, zcode_home: Path | None = None, target: str = "auto", apply: bool = False, dry_run: bool = False, replace: list[str] | tuple[str, ...] = ()) -> list[TargetPlan]:
    if apply and dry_run:
        raise SyncError("--apply and --dry-run cannot be used together.")
    homes = {"codex": codex_home or Path.home() / ".codex", "claude": claude_home or Path.home() / ".claude", "zcode": zcode_home or Path.home() / ".zcode"}
    plans = build_plans(repo, homes, target, replace)
    if apply:
        apply_plans(plans)
    return plans


def deploy_after_pull(repo: Path, *, codex_home: Path, claude_home: Path, zcode_home: Path | None = None, force: bool = False, dry_run: bool = False, apply: bool = False, pull: bool = False, target: str = "auto", replace: list[str] | tuple[str, ...] = ()) -> bool:
    if apply and dry_run:
        raise SyncError("--apply and --dry-run cannot be used together.")
    repo = repo.expanduser().resolve()
    homes = {"codex": codex_home, "claude": claude_home, "zcode": zcode_home or Path.home() / ".zcode"}
    parse_replacements(replace, resolve_target_names(target, homes))
    if pull and apply:
        try:
            pull_repository(repo)
        except (SyncError, OSError) as exc:
            if not force:
                raise
            print(f"Explicit git pull failed ({exc}); --force permits using the local sources, not overwriting conflicts.")
    elif pull:
        print("Preview: --pull is deferred until --apply; this plan uses local sources.")
    plans = build_plans(repo, homes, target, replace)
    print_plans(plans, apply=apply)
    if any(plan.conflicts for plan in plans):
        raise SyncError("Conflicts found; no target was modified.")
    if apply and plans:
        apply_plans(plans)
        print("Sync applied successfully." if any(plan.has_changes for plan in plans) else "Already up to date; no files were written.")
        for plan in plans:
            if plan.backup_root:
                print(f"[{plan.name}] Verified backups: {plan.backup_root}")
    return bool(plans)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Safely preview and sync instructions and skills to Claude Code, Codex and ZCode.")
    parser.add_argument("--target", choices=["auto", "all", *TARGETS], default="auto", help="Auto selects existing home paths; a named target or all can create missing homes.")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--apply", action="store_true", help="Write after preflight and verified backups; the default is preview only.")
    mode.add_argument("--dry-run", action="store_true", help="Compatibility alias for preview.")
    parser.add_argument("--pull", action="store_true", help="Explicit git pull --ff-only before planning, only with --apply; preview defers it.")
    parser.add_argument("-f", "--force", action="store_true", help="Continue after an explicit pull fails; never enables writes or overwrites conflicts.")
    parser.add_argument("--replace", metavar="TARGET:RELATIVE_PATH", action="append", default=[], help="Authorize one entry-block or skill-file content replacement (repeatable); still requires --apply and backups.")
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parent.parent, help="agent-kit repository root.")
    for name in TARGETS:
        parser.add_argument(f"--{name}-home", type=Path, default=Path.home() / f".{name}", help=f"Destination {name} home.")
    return parser.parse_args(argv)


def load_tests(loader, tests, pattern):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    return loader.loadTestsFromName("scripts.test_sync")


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if argv == ["test"]:
        result = unittest.TextTestRunner(verbosity=2).run(load_tests(unittest.defaultTestLoader, None, None))
        return 0 if result.wasSuccessful() else 1
    args = parse_args(argv)
    try:
        deploy_after_pull(args.repo, codex_home=args.codex_home, claude_home=args.claude_home, zcode_home=args.zcode_home, force=args.force, dry_run=args.dry_run, apply=args.apply, pull=args.pull, target=args.target, replace=args.replace)
    except (SyncError, OSError, UnicodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

---
name: init-project
description: Initialize or retrofit a repository with agent-native workflow files for Claude Code, Codex, and/or ZCode. Use when the user asks to set up, bootstrap, or dry-run project-level agent configuration, including CLAUDE.md, AGENTS.md, project-level skills directories, and optional git-hook maintainability audit reminders.
---

# Init Project

## Overview

Initialize a repository with agent-native project guidance for whichever coding
agents the user actually uses. Detect the active agent host first, then
generate only the files that host needs. Keep global instructions lean; derive
project guidance at runtime from inspected facts and user decisions.

## Workflow

1. Detect the agent context before proposing files.
   - Prefer the user's explicit target and the active runtime's host identity.
     `CLAUDECODE=1` is a Claude Code signal; a ZCode runtime identifies ZCode.
     Existing `.claude/`, `.codex/`, or `.zcode/` directories indicate possible
     targets, not the active host. `AGENTS.md` and `.agents/skills/` are shared
     by Codex and ZCode and do not distinguish them.
   - A repository may target multiple hosts. Ask only when the required target
     cannot be determined from the request, runtime, or project guidance.
2. Inspect the repository before proposing files.
   - Read `package.json`/`pyproject.toml`/equivalent manifests, existing
     `CLAUDE.md`/`AGENTS.md`, existing project skills directories
     (`.claude/skills/`, `.agents/skills/`, `.zcode/skills/`), and `docs/README.md` when they exist.
3. Ask only for missing decisions that affect generated files.
   - Technology stack and execution model: frameworks, package manager,
     runtime, Docker or local.
   - Documentation preference, language/style policies for code, UI copy,
     comments, docs, and commit messages. Inspect enough to propose concrete
     policies instead of recording generic "match existing".
   - UI localization policy when applicable.
   - Whether to opt into git-hook maintainability audit reminders, and the
     interval as a commit count (not days/weeks).
   - Whether to use the explicit audit marker trailer `Maintenance-Audit: true`.
4. Generate project guidance directly as the agent.
   - Claude Code targets: `CLAUDE.md` (long-lived rules), `.claude/skills/<project-skill>/SKILL.md` (reusable workflow detail).
   - Codex targets: `AGENTS.md` (long-lived rules), `.agents/skills/<project-skill>/SKILL.md`.
   - ZCode targets: `AGENTS.md` (long-lived rules), `.zcode/skills/<project-skill>/SKILL.md`.
   - When multiple hosts are targeted, keep their rule content consistent.
     Codex and ZCode share one `AGENTS.md`; put shared skills in `.agents/skills/`
     rather than duplicating them in `.zcode/skills/`. If Claude Code is also
     targeted, keep `CLAUDE.md` aligned and note the companion rule file.
   - Show or explain proposed changes before overwriting existing guidance.
5. Git-hook audit reminders (host-agnostic, lives in the repository).
   - When opted in, copy the agent-kit `core/git-hooks/` package into the
     repository as `.githooks/` plus `scripts/install-git-hooks.sh`, then have
     the user run the installer (Git Bash on Windows).
   - Record cadence with `git config --local agentkit.maintainabilityAuditInterval <N>`
     and, when HEAD exists and the user did not request marker-only baselines,
     `git config --local agentkit.maintainabilityAuditBaseline <head-sha>`.
   - The hook prints a non-blocking reminder: before the interval,
     `建议<N>次后进行项目审计。`; once reached, `上次审计是<N>次前，建议尽快安排审计。`
6. Preserve existing user work.
   - Never overwrite existing files without showing the diff first.
   - Merge with existing project guidance where practical.

## Project Information To Capture

Capture only facts stable and useful across future sessions: languages,
frameworks, package manager, runtime, Docker or local-first; explicit language
and style policies; required test/lint/typecheck/build/migration commands;
documentation preferences; UI localization policy; deployment providers;
safety-sensitive areas (migrations, permissions, auth, destructive ops);
maintainability audit policy.

Do not duplicate agent-host platform capabilities. See
[references/agent-locations.md](references/agent-locations.md) for official
file locations per host.

## Validation

- After generating files, verify: each generated `SKILL.md` has valid
  frontmatter (`name`, `description` only); referenced paths exist;
  `git config --local agentkit.maintainabilityAuditInterval` is set when the
  hook was opted in.

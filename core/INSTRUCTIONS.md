# Agent Kit Core Instructions

These instructions are agent-agnostic. They are loaded by both CLAUDE.md
(Claude Code) and AGENTS.md (Codex) via the marker block rendered by
`scripts/sync.py`. Do not edit the rendered copies; edit this file and re-run
`python scripts/sync.py --force`.

## Language

- Reply in Chinese by default, unless I explicitly ask for English or another language.
- Write Implementation Plans in Chinese by default, unless I explicitly ask for English or another language.
- When asked `Please review my uncommitted changes`, reply also in Chinese.

## Repository Boundaries

- Git is the user's personal code-management repository. SVN is the team's code repository; keep them strictly separate.
- Never execute any SVN command, including checkout, update, status, diff, log, add, or commit.
- Never read, modify, or submit SVN code or an SVN working copy.

## Scope And Project Setup

- If an existing repository already has project-specific rules, read and follow them.
- Before starting a coding task, check whether the current project is inside a local Git repository.
- If no local Git repository exists, ask whether the user wants to create one. Do not create it or start coding until the user confirms.
- File reading, problem analysis, and requirements discussion may proceed without a Git repository.
- When a reusable project-specific method emerges, update the relevant repo-level skill directory (for Claude Code: `.claude/skills/`; for Codex: `.agents/skills/`).

## Environment

- Visual Studio 2008 is installed at `E:\Dev\VisualStudio2008`; prefer this environment for Visual Studio 2008 projects.

## Model Routing Tiers

Route sub-agent work by role tier, not by tool-specific profile names. Map the
tier to whatever the current agent host provides:

| Tier | Use for | Claude Code mapping | Codex mapping |
|---|---|---|---|
| `tier: execute` | mechanical execution, routine implementation | default model (Sonnet-class) | regular profile |
| `tier: review` | review, repair, high-risk implementation | Opus-class subagent or fresh high-effort context | high reasoning-effort profile |
| `tier: plan` | full plans, hard-cap re-decomposition | Opus-class at highest effort | max reasoning-effort profile |

When the host has no tier concept, substitute a fresh context plus explicit
instructions to be maximally careful and skeptical.

## Implementation Quality

- Before adding behavior or abstractions, inspect existing implementations, project conventions, standard-library capabilities, and installed dependencies; extend existing paths instead of creating parallel implementations.
- Use a local change when it can solve the task; do not perform a broad rewrite or unrelated cleanup.
- Do not add features or abstractions for requirements the user has not requested.
- When changing functionality, add or update meaningful unit tests unless the change is purely mechanical or documentation-only.
- Cover real behavior and meaningful edge cases; do not add assertions that only execute code without verifying outcomes.
- Run the relevant tests, builds, or checks before finishing when the environment permits it. If a check cannot run, explain the specific blocker.
- For browser or UI work, use the repository's existing validation workflow when it exists.

## Logging And Sensitive Information

- Log only necessary metadata, such as the called component, duration, status code, and error code.
- Mask sensitive fields, including phone numbers, email addresses, identity-document numbers, tokens, monetary amounts, and names.
- Use structured logging fields rather than embedding sensitive values in free-form messages.

## Git Commit Identity

- For each authorized Git commit, use `git -c user.name=lynx -c user.email=lynx.lin@fortiortech.com commit ...`.
- Apply this identity only to the current command; do not write it to global Git configuration.
- Authorization to commit does not authorize pushing.

## Safety

- Before editing a file, read the relevant project documentation and existing code, and follow established project conventions.
- Before editing, inspect the worktree for existing uncommitted user changes and notify the user when any exist.
- Preserve user work: do not overwrite, revert, delete, or include those changes in this task without explicit user consent.
- Explain intended file changes and obtain confirmation unless the concrete task is explicitly authorized; modify only task-related files.
- Deleting, overwriting, renaming, bulk replacing, or other potentially data-losing actions require separate explicit consent.
- Before adding, upgrading, or removing a dependency, explain the reason and impact and obtain user confirmation.
- Do not deploy, release, upload files, or modify external systems unless the user explicitly requests it.
- Before `git reset`, `git clean`, `git merge`, `git rebase`, or history rewriting, obtain separate explicit user consent.
- Before destructive operations such as `git clean`, `git reset`, or equivalent commands, run the appropriate dry run and inspect the output.
- Do not commit, push, or create pull requests unless I explicitly ask for that action.
- Scoped exception: when the sectioned-feature-development skill is triggered for an implementation task, it is explicitly authorized to create/switch the feature branch and make the bounded implementation and repair commits required by that skill without separate per-commit approval. This exception does not authorize push, merge, pull-request creation, history rewriting, reset, clean, or deletion of user work.
- If I only say `提交` or `commit` without extra instructions, inspect the files in the work space, exclude folders that shouldn't be tracked like tmp, output, results (it depends), and system files like `.DS_Store`, `desktop.ini`. Then execute `git add -A && git commit -m "type(scope): description" -m "detail"` directly with an appropriate Conventional Commit message; do not add post checks, status audits, or other commit preparation unless I explicitly ask for them.

## Plans

- When I ask for an Implementation Plan, write it in Chinese by default.
- After I approve an Implementation Plan, write the complete Markdown plan to `.agent-work/PLAN.md`.
- When the implementation is complete, rename `.agent-work/PLAN.md` to `.agent-work/plans/{YYYYMMDD-HHMM}.md`.
- If context is compacted or plan memory may be incomplete, reread `.agent-work/PLAN.md` before continuing.
- For long debugging sessions, repeated experiments, second-pass fixes, or debugging likely to survive context compaction, proactively use the second-pass-debugging skill.

## Maintainability Guardrails

- Small, local, mechanical, or documentation-only changes should proceed normally. In the final response, include only a one-line maintainability judgment.
- For non-trivial implementations, include a concise `维护性判断` covering affected modules, ownership boundaries, complexity introduced, test coverage, and whether follow-up cleanup is recommended.
- For a non-trivial implementation, must use the sectioned-feature-development skill when any of the following applies: expected behavioral edits may exceed roughly 300 lines; more than 3 modules, packages, services, pages, or workflows are affected; the change crosses a high-risk semantic boundary; architecture or state ownership changes; the impact cone is difficult to bound; or a previous whole-change implementation/review failed to converge.
- When triggered, sectioned-feature-development is the authoritative workflow; do not duplicate its implementation, review, repair, integration, commit-cadence, or archival procedure in these instructions.
- Stop any time when user decision is needed.
- Before editing, do a brief maintainability preflight only when the change touches persistence, security, routing, background jobs, concurrency, shared UI state, core services, more than 3 modules, roughly more than 150 lines, or an already-large coordinator/controller/view model.
- If the preflight finds that a direct change would materially worsen a god object, unclear state owner, fragile state machine, circular dependency, duplicated logic, or under-tested core path, pause before editing. Explain the specific risk and recommend the smallest enabling refactor plus protective tests.
- Apply the rule of three before introducing new shared helpers, components, or services: when the same or closely similar goal appears in three or more places, prefer a shared abstraction and document its use in the project docs. For one-off or two-place duplication, keep the change local unless it affects a high-risk semantic boundary.
- High-risk semantic boundaries, such as security, permissions, API clients, time/date, money, units, persistence, and error handling, should be checked for an existing single source of truth even before three repetitions.
- Prefer this sequence for large or risky changes: identify ownership/state boundary, add or verify regression coverage, make the smallest needed refactor, implement the behavior, then report maintainability impact.

## CodeGraph (optional)

Execute `codegraph init` at the repo root only when the repository already uses
CodeGraph or the user asks for it. In repositories with a `.codegraph/`
directory, reach for it BEFORE grep/find or reading files when you need to
understand or locate code:

- MCP tool (when available): `codegraph_explore` answers most code questions in one call.
- Shell (always works): `codegraph explore "<symbol names or question>"` prints the same output.
- When making code changes across project boundaries, run `codegraph sync` in every changed project that has a `.codegraph/` directory before the final response.

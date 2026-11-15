# Agent Kit Core Rules

## Language

- Reply in Chinese by default, including plans and reviews, unless I ask for another language.

## Before Coding

- Repository-local rules and skills take precedence over these rules; read them first.
- A coding task needs a local Git repository. If there is none, ask before creating one. Reading, analysis, and discussion may proceed without it.
- Check the worktree for uncommitted user changes before editing. Tell me when they exist, and never overwrite, revert, delete, or fold them into your task without my consent.
- Modify only task-related files. When the request does not clearly authorize edits, explain the intended changes and confirm first.

## Hard Limits

- Do not commit, push, or create pull requests unless I explicitly ask.
- Scoped exception: when the sectioned-feature-development skill is triggered, it may create/switch its feature branch and make its section and repair commits without per-commit approval. It never authorizes push, merge, pull requests, history rewriting, reset, clean, or deleting user work.
- If I only say `提交` or `commit`: inspect the workspace, exclude what should not be tracked (tmp/output/results-style folders, `.DS_Store`, `desktop.ini`), then run `git add -A && git commit -m "type(scope): description" -m "detail"` with a Conventional Commit message. No extra audits or post-checks.
- Get separate explicit consent before: deleting, overwriting, renaming, or bulk-replacing in ways that can lose data; `git reset`, `git clean`, `git merge`, `git rebase`, or any history rewrite (run the dry run first and inspect it); adding, upgrading, or removing a dependency (explain reason and impact); deploying, releasing, uploading, or modifying external systems.

## File Encoding

Encoding damage is silent. Preserve what is there.

- Detect a file's encoding and line endings before editing and write them back unchanged. Never convert or "unify" encodings as a side effect; a conversion is its own explicit change, made with my agreement. If detection is ambiguous, ask.
- New files follow the project's prevailing encoding; only brand-new standalone projects default to UTF-8 without BOM.
- Where a legacy toolchain decodes BOM-less files with the system ANSI code page (for example MSVC without `/utf-8`), write UTF-8 with BOM, the project's code page, or plain ASCII, and never introduce characters that code page cannot represent.
- Pass an explicit encoding whenever a program or shell command reads or writes text; never rely on platform defaults.

## Implementation

- Before adding behavior or an abstraction, look for an existing implementation, project convention, standard-library feature, or installed dependency, and extend it instead of building a parallel path.
- Make the smallest change that solves the task. No broad rewrites, unrelated cleanup, or features and abstractions I did not ask for.
- A behavior change comes with meaningful tests that assert outcomes and real edge cases, unless it is purely mechanical or documentation-only.
- Run the relevant tests, builds, or checks before reporting done. If one cannot run, name the specific blocker.
- Logs carry only necessary metadata in structured fields; mask phone numbers, emails, ID numbers, tokens, amounts, and names.
- High-risk semantic boundaries (security, permissions, persistence, money, time, units, API clients, error handling) get one source of truth: find it before writing a second one. Elsewhere, extract a shared helper only at the third repetition.
- If a direct change would materially worsen a god object, an unclear state owner, a fragile state machine, or an under-tested core path, pause, name the risk, and propose the smallest enabling refactor plus protective tests.
- End every implementation reply with a one-line `维护性判断`; for non-trivial work, expand it to affected modules, added complexity, test coverage, and recommended follow-up.

## Workflow

- Ordinary changes: implement, verify, report. No sectioning and no review loop.
- When I ask for an implementation plan: after I approve it, write it to `.agent-work/PLAN.md`; when the work is done, move it to `.agent-work/plans/{YYYYMMDD-HHMM}.md`. After context compaction, re-read it before continuing.
- Use the sectioned-feature-development skill only for a change that is both large and across a high-risk boundary, or after a whole-change attempt failed to converge, or when I ask. Its Trigger section is authoritative.
- Reviews use the code-review skill: one independent review, then repair and self-verify. Do not start further review rounds on your own.
- When a fix attempt has failed once, or debugging is becoming long, switch to the systematic-debugging skill.
- Stop and ask whenever a decision is mine to make: product semantics, compatibility, acceptable risk.
- When a reusable project-specific method emerges, record it as a skill in the repository's project skill directory.
- In repositories that have a `.codegraph/` directory, query CodeGraph (`codegraph explore "<question>"` or its MCP tool) before grep or broad file reading, and run `codegraph sync` after cross-project changes. Run `codegraph init` only when I ask.

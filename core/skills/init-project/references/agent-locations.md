# Official File Locations Per Agent Host

Avoid inventing parallel conventions; write to the locations each host reads.

## Claude Code

- User-level instructions: `~/.claude/CLAUDE.md`
- Project-level instructions: `CLAUDE.md` at repository root (auto-loaded)
- Project skills: `.claude/skills/<name>/SKILL.md`
- User-level skills: `~/.claude/skills/<name>/SKILL.md`

## Codex

- User-level instructions: `~/.codex/AGENTS.md` (GUI: Settings - Personalization - Custom instructions)
- Project-level instructions: `AGENTS.md` at repository root
- Project skills: `.agents/skills/<name>/SKILL.md`
- User-level skills: `~/.codex/skills/<name>/SKILL.md`

## Shared (host-agnostic)

- Working state: `.agent-work/` (plans, section artifacts, debug notes, audit ledgers)
- Worktree workspace: `.worktrees/` with `.worktrees/current-agents/` registry
- Git hooks: `.githooks/` + repository-local `core.hooksPath`

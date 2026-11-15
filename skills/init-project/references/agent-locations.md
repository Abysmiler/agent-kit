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

## ZCode

- User-level instructions: `~/.zcode/AGENTS.md` (not `CLAUDE.md`)
- Project-level instructions: `AGENTS.md` at repository root; shared with Codex when both are targeted
- Project skills: `.zcode/skills/<name>/SKILL.md`; also reads `.agents/skills/`
- User-level skills: `~/.zcode/skills/<name>/SKILL.md`; also reads `~/.agents/skills/`
- User configuration: `~/.zcode/cli/config.json`; project configuration: `.zcode/config.json` or `zcode.json`. These are not distributed by agent-kit.
- User instructions load before project instructions. Skills load user scope before project scope, with `.zcode` before `.agents` within a scope; the first same-named skill wins. Avoid duplicate copies.

Verified against ZCode's bundled `zcode-guide` 0.1.0 configuration guide.

## Shared (host-agnostic)

- Working state: `.agent-work/` (plans, section artifacts, debug notes, audit ledgers)
- Worktree workspace: `.worktrees/` with `.worktrees/current-agents/` registry
- Git hooks: `.githooks/` + repository-local `core.hooksPath`

<!-- 中文翻译版；英文原版为本目录同名 .md 文件。若两者不一致，以英文版为准。 -->

# 各代理宿主的官方文件位置

避免发明平行约定；写入各宿主实际读取的位置。

## Claude Code

- 用户级指令：`~/.claude/CLAUDE.md`
- 项目级指令：仓库根目录的 `CLAUDE.md`（自动加载）
- 项目技能：`.claude/skills/<name>/SKILL.md`
- 用户级技能：`~/.claude/skills/<name>/SKILL.md`

## Codex

- 用户级指令：`~/.codex/AGENTS.md`（GUI：Settings - Personalization - Custom instructions）
- 项目级指令：仓库根目录的 `AGENTS.md`
- 项目技能：`.agents/skills/<name>/SKILL.md`
- 用户级技能：`~/.codex/skills/<name>/SKILL.md`

## 共享（与宿主无关）

- 工作状态：`.agent-work/`（计划、章节（section）产物、调试笔记、审计台账）
- Worktree 工作区：`.worktrees/` 及 `.worktrees/current-agents/` 注册表
- Git hooks：`.githooks/` + 仓库本地 `core.hooksPath`

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

## ZCode

- 用户级指令：`~/.zcode/AGENTS.md`（不是 `CLAUDE.md`）
- 项目级指令：仓库根目录的 `AGENTS.md`；同时面向 Codex 时共用此文件
- 项目技能：`.zcode/skills/<name>/SKILL.md`；也读取 `.agents/skills/`
- 用户级技能：`~/.zcode/skills/<name>/SKILL.md`；也读取 `~/.agents/skills/`
- 用户配置：`~/.zcode/cli/config.json`；项目配置：`.zcode/config.json` 或 `zcode.json`。agent-kit 不分发这些配置。
- 用户指令先于项目指令加载。技能先扫描用户级再扫描项目级，同一作用域内 `.zcode` 先于 `.agents`；同名技能首个匹配生效，避免重复放置。

依据 ZCode 随附的 `zcode-guide` 0.1.0 配置指南核实。

## 共享（与宿主无关）

- 工作状态：`.agent-work/`（计划、章节（section）产物、调试笔记、审计台账）
- Worktree 工作区：`.worktrees/` 及 `.worktrees/current-agents/` 注册表
- Git hooks：`.githooks/` + 仓库本地 `core.hooksPath`

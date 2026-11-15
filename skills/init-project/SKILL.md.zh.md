<!-- 中文翻译版；英文原版为本目录同名 .md 文件。若两者不一致，以英文版为准。 -->

---
name: init-project
description: Initialize or retrofit a repository with agent-native workflow files for Claude Code, Codex, and/or ZCode. Use when the user asks to set up, bootstrap, or dry-run project-level agent configuration, including CLAUDE.md, AGENTS.md, project-level skills directories, and optional git-hook maintainability audit reminders.
---

# 初始化项目（Init Project）

## 概述

为用户实际使用的编码代理初始化仓库的代理原生项目指引。先检测活动的代理宿主，
然后只生成该宿主需要的文件。保持全局指令精简；项目指引在运行时从检查到的
事实与用户决策中派生。

## 工作流

1. 在提出文件方案之前，先检测代理上下文。
   - 优先采用用户明确指定的目标与当前运行时的宿主身份。
     `CLAUDECODE=1` 是 Claude Code 的信号；ZCode 运行时表明当前宿主为 ZCode。
     已有 `.claude/`、`.codex/` 或 `.zcode/` 目录仅表明可能使用的宿主，
     不能据此判断当前宿主。`AGENTS.md` 与 `.agents/skills/` 由 Codex 和
     ZCode 共用，不能用于区分二者。
   - 一个仓库可以面向多个宿主。仅当无法从请求、运行时或项目指引确定
     所需目标时，才询问用户。
2. 在提出文件方案之前，先检查仓库。
   - 阅读 `package.json`/`pyproject.toml`/等价的清单文件、已存在的
     `CLAUDE.md`/`AGENTS.md`、已存在的项目技能目录
     (`.claude/skills/`、`.agents/skills/`、`.zcode/skills/`)，以及存在时的 `docs/README.md`。
3. 只询问影响生成文件的缺失决策。
   - 技术栈与执行模型：框架、包管理器、运行时、Docker 还是本地。
   - 文档偏好，代码、UI 文案、注释、文档与提交信息的语言/风格策略。
     做足检查以提出具体策略，而不是记录笼统的"与现有一致"。
   - 适用时的 UI 本地化策略。
   - 是否选择加入 git-hook 维护性审计提醒，以及以提交次数（而非
     天/周）表示的间隔。
   - 是否使用显式审计标记 trailer `Maintenance-Audit: true`。
4. 由代理直接生成项目指引。
   - Claude Code 目标：`CLAUDE.md`（长期规则）、`.claude/skills/<project-skill>/SKILL.md`（可复用的工作流细节）。
   - Codex 目标：`AGENTS.md`（长期规则）、`.agents/skills/<project-skill>/SKILL.md`。
   - ZCode 目标：`AGENTS.md`（长期规则）、`.zcode/skills/<project-skill>/SKILL.md`。
   - 同时面向多个宿主时，保持规则内容一致。Codex 与 ZCode 共用一个
     `AGENTS.md`；共享技能放在 `.agents/skills/`，不要再复制到 `.zcode/skills/`。
     若同时面向 Claude Code，保持 `CLAUDE.md` 内容同步并注明配套规则文件。
   - 覆盖已有指引之前，先展示或解释拟议的改动。
5. Git-hook 审计提醒（与宿主无关，位于仓库内）。
   - 选择加入后，将 agent-kit 的 `core/git-hooks/` 包复制进仓库，
     成为 `.githooks/` 加 `scripts/install-git-hooks.sh`，然后让
     用户运行安装器（Windows 上为 Git Bash）。
   - 用 `git config --local agentkit.maintainabilityAuditInterval <N>` 记录节奏，
     并且当 HEAD 存在且用户未要求仅标记基线时，
     `git config --local agentkit.maintainabilityAuditBaseline <head-sha>`。
   - 该 hook 打印非阻塞提醒：间隔未到时为
     `建议<N>次后进行项目审计。`；到达后为 `上次审计是<N>次前，建议尽快安排审计。`
6. 保护既有用户工作。
   - 绝不先展示 diff 就覆盖既有文件。
   - 在可行处与既有项目指引合并。

## 需要采集的项目信息

只采集在未来会话中稳定且有用的事实：语言、框架、包管理器、运行时、
Docker 还是本地优先；显式的语言与风格策略；必需的测试/lint/类型检查/
构建/迁移命令；文档偏好；UI 本地化策略；部署提供商；
安全敏感区域（迁移、权限、认证、破坏性操作）；维护性审计策略。

不要重复代理宿主平台自身的能力。各宿主的官方文件位置参见
[references/agent-locations.md](references/agent-locations.md)。

## 验证

- 生成文件后，核验：每个生成的 `SKILL.md` 都有有效的
  frontmatter（仅 `name`、`description`）；被引用的路径存在；
  选择加入了 hook 时，`git config --local agentkit.maintainabilityAuditInterval` 已设置。

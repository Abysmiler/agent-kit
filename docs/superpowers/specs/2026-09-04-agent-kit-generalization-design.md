# agent-kit 通用化重构设计

日期：2026-09-04
来源：对 AGENTS.md-main（Codex 个人约束仓库）的通用化重构
状态：已获用户批准的设计

## 背景与目标

原仓库是一套面向 OpenAI Codex CLI 的个人 Agent 治理体系（AGENTS.md 规则 + 9 个技能 + git hooks + 模型路由 + 分发脚本）。设计思想先进（状态外置、评审反锚定、收敛即分解、范围化授权），但存在私人环境硬编码、Codex 专属依赖、两处正面文档冲突、Unix-only 假设等问题。

目标：重构为**代理无关、Windows 优先跨平台、可直接安装使用**的项目，同时支持 Claude Code（优先）与 Codex。

## 已确认的需求决策

| 决策点 | 结论 |
|---|---|
| 目标代理 | Claude Code 优先 + Codex 双支持 |
| 保留范围 | 全部核心链路（8 技能 + hooks + init）；删 feishu-message-sender；删 RESEARCH 目录 |
| 模型路由 | sol_* 四档抽象为三级角色档位（execute / review / plan） |
| 环境假设 | Windows 优先跨平台；删 colima/docker-compose/飞书等私人偏好 |
| 新项目位置 | `E:\rpo\AGENTS.md-main\agent-kit\`（当前目录子目录，原仓库不动） |
| 文档语言 | 技能正文英文；面向用户的模板/报告/README 中文 |
| 冲突统一 | 收敛准则统一为"单次干净即可"；worktree 统一走 manual-git-worktrees 注册表 |
| 分发方式 | 双目标分发脚本（~/.codex 与 ~/.claude） |
| git hook | 保留并通用化 |
| 内容深度 | 保留全部内容深度，仅做通用化手术，不压缩篇幅 |
| init 技能 | 重写为双代理版（探测代理类型生成对应配置） |

## 总体结构

```
agent-kit/
├── core/
│   ├── INSTRUCTIONS.md          # 代理无关的核心规则正文（唯一事实来源，约 60 行）
│   ├── skills/                  # 8 个技能
│   │   ├── sectioned-feature-development/
│   │   ├── code-review/
│   │   ├── code-audit/
│   │   ├── second-pass-debugging/
│   │   ├── debug-notes-to-engineering-notes/
│   │   ├── grill-me/
│   │   ├── init-project/        # 原 init-codex-project 重写
│   │   └── manual-git-worktrees/
│   └── git-hooks/               # 6 个 hook + install-git-hooks.sh
├── adapters/
│   ├── codex/
│   │   ├── AGENTS.md            # 构建产物：Codex 入口 + 展开的 core 规则
│   │   └── agents/              # 4 个 toml（修正 sol_high 名实不符）
│   └── claude/
│       └── CLAUDE.md            # 构建产物：Claude 入口 + 展开的 core 规则
├── scripts/
│   ├── sync.py                  # 双目标分发
│   └── section_plan.py          # 从原技能迁入（已跨平台）
└── README.md                    # 中文：安装说明 + 能力地图
```

删除项（不迁移）：`skills/feishu-message-sender/`、`RESEARCH/` 全部 4 个文档、`git-hook.md`（内容并入 README 与 init-project 技能）、`sync_codex_config.py`（被 sync.py 取代）。

## 关键机制

### 1. 构建式分发（sync.py）

- `core/INSTRUCTIONS.md` 是规则唯一事实来源。
- 分发时把 core 正文渲染进 adapter 入口文件的机器标记区块（`<!-- AGENT-KIT:CORE:START -->` … `<!-- AGENT-KIT:CORE:END -->`，手法继承自原仓库 PLAN-FULL 的 SECTION 标记）。
- 标记区块之外的内容（各代理的入口说明、加载指引）由 adapter 文件自带，分发不覆盖。
- `core/skills/` 整目录复制到 `~/.codex/skills/` 与 `~/.claude/skills/`（原子替换，继承原 sync 脚本的临时文件 + rename 设计）。
- `core/git-hooks/` 不进用户目录，属于项目级基础设施，由 init-project 技能在各项目里引导安装。
- CLI：`--target codex|claude|all`（默认 all）、`--dry-run`、`--force`、`--codex-home`、`--claude-home`。
- 实现：pathlib、类型注解、原子替换、SyncError 统一退出码。Windows 优先（Git Bash 与 PowerShell 均可运行 `python scripts/sync.py`）。

### 2. 模型路由抽象（三级角色档位）

| 角色档位 | 用途 | Claude Code 映射 | Codex 映射 |
|---|---|---|---|
| `tier: execute` | 机械执行、常规实现 | 默认模型（Sonnet 级） | 常规 profile |
| `tier: review` | 评审、修复、高风险实现 | Opus 级 / 高推理子代理 | 高推理努力 profile |
| `tier: plan` | 完整计划、hard-cap 重分解 | Opus 最高档 | 最高推理 profile |

- 技能正文中所有 `subagent://sol_*` 引用改写为 `[tier: review]` 中性标记，并附通用说明："映射到当前代理可用的高推理档子代理或全新会话；无档位概念时用全新上下文 + 提高谨慎度代替"。
- `adapters/codex/agents/*.toml` 修正名实不符：sol_high.toml 的 effort 从 xhigh 改为 high；若目标模型不支持 high 档则删除该文件合并为三档。
- 角色档位表写入 core/INSTRUCTIONS.md 的 Routing 段，adapter 入口各自附映射示例。

### 3. 规则正文改写要点（core/INSTRUCTIONS.md）

保留原 AGENTS.md 骨架，手术清单：

**删除**：
- Docker/colima 段全部
- 飞书相关一切引用
- `docker-compose` 拼写偏好

**修改**：
- 模型 profile 引用 → 角色档位表
- `$skill` 语法 → 中性写法（"use the sectioned-feature-development skill"）
- CodeGraph 段改为可选："if the repo has a `.codegraph/` directory"（保留，因为它是条件触发的，不构成硬依赖）

**保留（精华）**：
- Language 段（中文回复/中文计划）
- Scope 段（项目规则优先、沉淀到项目 skills）
- Implementation Quality 全段
- Safety 全段（含对 sectioned-feature-development 的范围化提交授权例外、'提交'快捷通道）
- Plans 段（.agent-work/PLAN.md 生命周期）
- Maintainability Guardrails 全段（300 行/3 模块/高风险边界触发、预检清单、三次法则、高风险边界单一事实来源）
- 新增一小段：跨代理通用说明（本规则同时被 CLAUDE.md 与 AGENTS.md 加载）

### 4. 技能手术清单（逐技能）

| 技能 | 手术 |
|---|---|
| sectioned-feature-development | (a) 收敛准则统一：SKILL.md、integration-and-convergence.md 中"2 连干净"全部改为"单次覆盖完整的干净评审即可接受（无修复时）；有修复时审 repair delta + 影响锥后干净即可"；(b) worktree 约定统一：retry worktree 纳入 `.worktrees/` + current-agents 注册表；(c) `agents/openai.yaml` → `meta.yaml`（通用元信息）；(d) 去 sol_* 引用改 tier 标记 |
| code-review | section-review-protocol.md 的"单次干净"表述成为权威准则；去 sol_*；其余不动 |
| code-audit | anti-bloat.md 删私人路径；去 sol_*；其余不动 |
| second-pass-debugging | 仅去 `$` 语法 |
| debug-notes-to-engineering-notes | 仅去 `$` 语法 |
| grill-me | 不动（已干净） |
| init-project（重写） | 双代理探测：读环境（CLAUDE.md/CLAUDECODE=1 vs AGENTS.md/.codex）判断当前代理；生成项目级 CLAUDE.md 和/或 AGENTS.md；git hook 间隔配置与 install 引导保留；去除 .codex/config.toml、.agents/skills/ 的 Codex 专属约定，改为按代理生成对应结构（Claude: .claude/skills/；Codex: .agents/skills/） |
| manual-git-worktrees | 成为唯一 worktree 权威约定；新增一句被 SFD 引用的说明 |

### 5. git-hooks 通用化

- 核心 hook 逻辑不动（已跨平台、防御性好）。
- `install-git-hooks.sh` 增强：检测 zip 解压丢失执行位的情况，在设置 hooksPath 前对 `.githooks/` 下脚本 `chmod +x`（Git Bash 下有效）；文档说明 Windows 需在 Git Bash 运行。
- `Maintenance-Audit: true` trailer 机制原样保留。

## 内容深度约束

按用户决策"保留深度"：所有技能的 references/assets/scripts 全部迁移，仅做上述手术，不删减内容篇幅。唯一删除的是 feishu-message-sender 整个技能与 RESEARCH 目录。

## 测试与验证

1. **sync.py 单元测试**：内联 unittest（零外部依赖，与原 section_plan.py 的测试风格一致）覆盖渲染标记区块、原子替换、--dry-run、目标选择。
2. **section_plan.py**：迁移后运行其自带测试（138 行前向测试），确保零改动迁移可用。
3. **渲染验证**：sync 后检查 adapters/codex/AGENTS.md 与 adapters/claude/CLAUDE.md 的标记区块内容与 core/INSTRUCTIONS.md 一致。
4. **冲突修复验证**：grep 新仓库确认无 "two consecutive clean" / "2 连续干净" 残留；确认 sol_ 引用清零；确认私人路径（/Users/）清零。
5. **hook 验证**：在测试仓库安装 hook，提交验证提醒出现、trailer 重置计数。

## 明确不做（YAGNI）

- 不做 zcode 适配（用户未选）
- 不做 Claude Code 插件市场形态（.claude-plugin）
- 不做中文正文（保持正文英文 + 模板中文）
- 不压缩技能篇幅
- 不迁移 RESEARCH 研究文档
- 不改造 feishu 技能

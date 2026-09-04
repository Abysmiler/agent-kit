# agent-kit

代理无关的编码代理约束套件：一份核心规则 + 8 个技能 + git 审计提醒钩子，
同时支持 **Claude Code** 与 **Codex**。

## 快速开始

```bash
# 1. 分发到 ~/.claude 与 ~/.codex（默认双目标）
python scripts/sync.py --force

# 只装 Claude Code 一侧
python scripts/sync.py --force --target claude

# 预览不写入
python scripts/sync.py --dry-run

# 2. 新项目初始化：在目标仓库里对代理说"用 init-project 技能初始化这个项目"
#    它会探测当前代理（Claude Code / Codex），生成项目级 CLAUDE.md / AGENTS.md，
#    并可选安装 git 审计提醒钩子。
```

分发内容：
- `~/.claude/CLAUDE.md` / `~/.codex/AGENTS.md` — 入口文件（含渲染后的核心规则）
- `~/.claude/skills/` / `~/.codex/skills/` — 全部 8 个技能

修改规则的正确方式：编辑 `core/INSTRUCTIONS.md`（唯一事实来源）或技能文件，
再运行 `python scripts/sync.py --force`。不要直接编辑 adapters 下的渲染区块。

## 目录结构

```
agent-kit/
├── core/
│   ├── INSTRUCTIONS.md       # 代理无关核心规则（唯一事实来源）
│   ├── skills/               # 8 个技能（正文英文、面向用户模板中文）
│   └── git-hooks/            # 审计提醒钩子 + 安装脚本
├── adapters/
│   ├── claude/CLAUDE.md      # Claude Code 入口（含渲染核心规则区块）
│   └── codex/
│       ├── AGENTS.md         # Codex 入口（含渲染核心规则区块）
│       └── agents/           # 三档 tier profile（toml）
├── scripts/
│   ├── sync.py               # 双目标分发（内联测试：python scripts/sync.py test）
│   └── section_plan.py       # section 计划校验/提取工具
└── docs/superpowers/         # 设计文档与实施计划
```

## 能力地图（8 技能）

| 技能 | 用途 | 触发方式 |
|---|---|---|
| sectioned-feature-development | 大功能分节开发：冻结契约→逐节实现→独立评审→硬帽自动重分解 | 条件强制（>300 行 / >3 模块 / 跨高风险边界 / 架构变更 / 前次不收敛） |
| code-review | 有界变更的高级评审（STANDARD/SECTION/DELTA/INTEGRATION 四模式） | 评审请求时 |
| code-audit | 周期性全系统审计（持久化覆盖账本，跨周期深化） | 显式请求 / 审计提醒 |
| second-pass-debugging | 第一次修复失败后的系统化调试（证据盘点→单一假设→最小修复） | 第二次修复失败 / 长调试会话 |
| debug-notes-to-engineering-notes | 把调试记录沉淀为工程笔记 | 显式请求 |
| grill-me | 需求访谈：只问人拥有的产品语义决策 | 显式请求 |
| init-project | 项目初始化：探测代理类型，生成项目级配置与 git hooks | 显式请求 |
| manual-git-worktrees | 隔离 worktree 开发 + 多代理范围冲突注册表 | 显式请求 |

## 模型档位

技能正文用三级角色档位路由子代理工作，各代理自行映射：

| 档位 | 用途 | Claude Code | Codex |
|---|---|---|---|
| `tier: execute` | 机械执行、常规实现 | 默认模型（Sonnet 级） | tier-execute profile |
| `tier: review` | 评审、修复、高风险实现 | Opus 级子代理 | tier-review profile |
| `tier: plan` | 完整计划、硬帽重分解 | Opus 最高档 | tier-plan profile |

Codex 的三档 profile 位于 `adapters/codex/agents/*.toml`（模型名默认
gpt-5.6-sol，按需替换）。sync.py 不自动安装它们——Codex 用户需手动复制：
`cp adapters/codex/agents/*.toml ~/.codex/agents/`。宿主无档位概念时，
用全新上下文 + 提高谨慎度代替。

## Git Hook 审计提醒

非阻塞的提交计数提醒，提示何时该做一次可维护性审计：

```bash
# 项目内安装（init-project 技能会引导完成；Windows 需在 Git Bash 运行）
cp -r <agent-kit>/core/git-hooks/. .githooks/
cp <agent-kit>/core/git-hooks/install-git-hooks.sh scripts/
./scripts/install-git-hooks.sh

# 配置间隔（N 次提交提醒一次）
git config --local agentkit.maintainabilityAuditInterval 50
# 可选基线（默认取当前 HEAD）
git config --local agentkit.maintainabilityAuditBaseline <sha>
```

- 审计完成后提交消息带 `Maintenance-Audit: true` trailer，计数自动重置
- 提示输出到 stderr，永远 exit 0，不阻塞提交
- 环境变量 `AGENTKIT_MAINTAINABILITY_AUDIT_REMINDER=0` 可临时静默

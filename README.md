# agent-kit

代理无关的编码代理约束套件：一份核心规则 + 8 个技能 + git 审计提醒钩子，
同时支持 **Claude Code**、**Codex** 与 **ZCode**。

## 快速开始

```bash
# 1. 预览（默认行为）：读取所有已存在的宿主配置目录，只打印计划，不写入
python scripts/sync.py

# 预览、但只针对某一侧
python scripts/sync.py --target claude

# 2. 应用：重新计算并检查当前计划（--apply 才会写）
python scripts/sync.py --apply

# 只写入某个宿主；--target 会显式创建对应缺失目录
python scripts/sync.py --apply --target zcode

# 面向全部三侧，并显式创建缺失目录
python scripts/sync.py --apply --target all

# --dry-run 保证零写入（包括不执行 --pull，仅预览 + 打印推迟提示）
python scripts/sync.py --dry-run --pull

# 3. 新项目初始化：在目标仓库里对代理说"用 init-project 技能初始化这个项目"
#    它会探测当前代理（Claude Code / Codex / ZCode），生成项目级 CLAUDE.md / AGENTS.md，
#    并可选安装 git 审计提醒钩子。
```

## 使用方法

以下命令均在 `agent-kit` 项目根目录执行，脚本路径使用相对路径。

### 1. 预览同步计划

```bash
python scripts/sync.py
```

默认只检查已经存在的宿主目录并输出计划，不创建目录、不修改文件。也可以只预览某个宿主：

```bash
python scripts/sync.py --target zcode
python scripts/sync.py --target codex
python scripts/sync.py --target claude
```

### 2. 应用同步计划

确认预览结果没有冲突后，再执行：

```bash
python scripts/sync.py --apply
```

只同步 ZCode：

```bash
python scripts/sync.py --apply --target zcode
```

如果目标目录尚不存在，必须显式指定目标；脚本会创建对应目录：

```bash
python scripts/sync.py --apply --target all
```

### 3. 拉取最新仓库内容后同步

`--pull` 只在应用模式下执行，预览模式不会拉取：

```bash
python scripts/sync.py --apply --pull
```

如果明确允许在拉取失败时继续使用本地来源，可加 `--force`。它不会绕过同步冲突，也不会单独开启写入：

```bash
python scripts/sync.py --apply --pull --force
```

### 4. 处理明确确认的冲突

发生内容冲突时，先人工检查冲突文件；确认覆盖后，使用按文件授权的 `--replace`：

```bash
python scripts/sync.py --apply --target zcode --replace zcode:AGENTS.md
python scripts/sync.py --apply --target zcode --replace zcode:skills/code-review/SKILL.md
```

可以重复传入多个 `--replace`。它只授权指定文件，仍会执行路径检查、快照检查和备份。

### 5. 检查同步结果

同步成功后，宿主目录中应包含对应入口和技能目录：

- Claude Code：`~/.claude/CLAUDE.md`、`~/.claude/skills/`
- Codex：`~/.codex/AGENTS.md`、`~/.codex/skills/`
- ZCode：`~/.zcode/AGENTS.md`、`~/.zcode/skills/`

同步状态记录在各宿主目录的 `.agent-kit/manifest.json`，被替换文件的备份位于
`.agent-kit/backups/<batch-id>/`。脚本不会修改宿主的 `cli/config.json`、`settings.json` 或插件配置。

## 同步语义

`scripts/sync.py` 默认 **只预览、不写入**。要实际修改目标需加 `--apply`。它把
`core/INSTRUCTIONS.md`（唯一事实来源）渲染进各宿主入口文件的
`<!-- AGENT-KIT:CORE:START/END -->` 标记块，再把 `core/skills/` 分发给各宿主，
并在每个宿主下维护 `<home>/.agent-kit/manifest.json` 状态与
`.agent-kit/backups/<batch-id>/` 备份。该 `.agent-kit/` 目录不属于任何宿主的
skill 扫描路径。

| 参数 | 说明 |
|---|---|
| `--target {auto,all,codex,claude,zcode}` | `auto`（默认）只选择已存在的宿主配置目录，不通过软件安装状态猜测；已存在但类型不安全的路径会报告冲突。具名目标或 `all` 配合 `--apply` 才会创建缺失目录。 |
| `--apply` | 根据当前文件重新计算计划，经预检后写入；并非执行上次预览的冻结快照。没有此参数时只预览。 |
| `--dry-run` | 只预览，与 `--apply` 互斥；若同时传 `--pull`，打印推迟提示，不执行拉取。 |
| `--pull` | 仅在 `--apply` 时执行 `git pull --ff-only`，随后根据更新后的本地来源重新预检。预览模式只打印推迟提示。 |
| `--force` | 仅允许显式 `--pull` 失败后继续同步；**不绕过冲突、不启用写入**。 |
| `--replace TARGET:RELATIVE_PATH` | 可重复，如 `--replace zcode:skills/code-review/SKILL.md` 或 `--replace zcode:AGENTS.md`。只授权对应文件的内容替换；覆盖已有文件前仍须备份，不绕过路径安全、manifest 损坏或坏标记检查。 |

### 入口文件（各宿主）

- 入口不存在 → 生成新文件。
- 有完整唯一标记块 → 只更新块内文本，块外宿主说明与翻译原样保留。
- 无标记 → 备份原文件并校验后整文件替换；旧的自定义规则不再生效。
- 标记损坏或重复 → 始终冲突。
- manifest 记录块哈希：块内出现本地修改时冲突；无可信历史且块与当前来源
  不同也须显式 `--replace`；已有块与来源相同则可接管。

### 技能（按文件哈希保护）

- 用户新文件保留。
- 同名未管理且内容不同 → 冲突。
- 用户修改过、源未变 → 保留（preserve）。
- 双方都改 → 冲突。
- 文件已等于新版 → 可接管。
- 用户删除文件 → 不擅自恢复；源再变时报告冲突。
- 来源删除文件 → 只报 stale，不删除。

### 安全与原子性

- 所有目标先全量预检：任何目标有冲突，则零目标写入。
- 应用前复查快照；全部目标完成备份并校验后才写配置文件；每个文件原子替换。
- 捕获运行时失败时尝试回滚；回滚若失败必须提示备份位置。
- 不承诺断电 / 进程被强杀下跨目录事务的原子性。
- 绝不修改 `cli/config.json`、`settings.json`、`plugins` 等宿主运行配置。
- 同步在内存渲染，不再反写仓库内 adapter 文件（adapters 下的渲染块用于生成与校验）。

修改规则的正确方式：编辑 `core/INSTRUCTIONS.md`（唯一事实来源）或技能文件，
再运行 `python scripts/sync.py --apply`。不要直接编辑 adapters 下的渲染区块；
那些渲染块由本脚本从 `core/INSTRUCTIONS.md` 生成。

### ZCode 结构说明

ZCode 的结构与 Claude Code **不完全相同**：指令名是 `AGENTS.md`，不是
`CLAUDE.md`；运行配置位于 `~/.zcode/cli/config.json`，本脚本不会改动它，
也不会把技能装进 `.zcode/cli/skills/`。项目规则使用仓库根目录的 `AGENTS.md`，
项目技能使用 `.zcode/skills/`（也兼容 `.agents/skills/`）。上述位置已对照
ZCode 自带的 `zcode-guide` 0.1.0 核实，来源和加载顺序见
[宿主文件位置](core/skills/init-project/references/agent-locations.md)。
同步后在 ZCode 的 Settings → Skills 或 `/` 菜单检查技能是否可见。

## 中文翻译版

每个英文文档在同目录下有对应的 `*.zh.md` 中文翻译版（如 `SKILL.md` →
`SKILL.md.zh.md`），供人阅读。翻译版不参与 sync.py 分发——代理始终加载
英文原版（frontmatter 元数据与机器标记以英文为准）。若中英不一致，以英文版为准。

## 目录结构

```
agent-kit/
├── core/
│   ├── INSTRUCTIONS.md       # 代理无关核心规则（唯一事实来源）
│   ├── skills/               # 8 个技能（正文英文、面向用户模板中文）
│   └── git-hooks/            # 审计提醒钩子 + 安装脚本
├── adapters/
│   ├── claude/CLAUDE.md      # Claude Code 入口（含渲染核心规则区块）
│   ├── zcode/AGENTS.md       # ZCode 入口（含渲染核心规则区块）
│   └── codex/
│       ├── AGENTS.md         # Codex 入口（含渲染核心规则区块）
│       └── agents/           # 三档 tier profile（toml）
├── scripts/
│   ├── sync.py               # 安全预览/应用分发（默认预览；内联测试：python scripts/sync.py test）
│   └── section_plan.py       # section 计划校验/提取工具
└── README.md
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

| 档位 | 用途 | Claude Code | Codex | ZCode |
|---|---|---|---|---|
| `tier: execute` | 机械执行、常规实现 | 默认模型（Sonnet 级） | tier-execute profile | 已配置的默认模型 |
| `tier: review` | 评审、修复、高风险实现 | Opus 级子代理 | tier-review profile | 全新审查上下文 |
| `tier: plan` | 完整计划、硬帽重分解 | Opus 最高档 | tier-plan profile | 全新规划上下文 |

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

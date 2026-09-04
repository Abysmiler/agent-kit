<!-- 中文翻译版；英文原版为本目录同名 .md 文件。若两者不一致，以英文版为准。 -->

# 产物模式与生命周期

本参考文档定义该工作流使用的持久产物，以及确定性辅助脚本。

## 目录

1. [`PLAN-FULL.md`](#1-plan-fullmd)
2. [`PLAN.md`](#2-planmd)
3. [`FEATURE-STATE.md`](#3-feature-statemd)
4. [`{ID}-CONTRACT.md`](#4-id-contractmd)
5. [`{ID}-HANDOFF.md`](#5-id-handoffmd)
6. [评审文件](#6-评审文件)
7. [硬上限重规划文件](#7-硬上限重规划文件)
8. [归档生命周期](#8-归档生命周期)
9. [辅助脚本命令](#9-辅助脚本命令)

## 1. `PLAN-FULL.md`

用途：权威功能契约、需求覆盖、章节谱系/依赖图、集成门禁，以及所有活跃章节规格。

必需的顶层内容：

- 功能元数据与确切基点。
- 目标、用户/运维行为、非目标与全局不变量。
- 权威来源与硬约束。
- 完整验收标准与校验命令。
- 所有权/状态边界图。
- 需求覆盖矩阵。
- 章节索引、谱系与依赖图。
- 集成检查点计划。
- 发布、回滚、迁移、开关、可观测性与清理计划。
- 决策与延后工作台账。

使用精确的标记，使 `scripts/section_plan.py` 能提取稳定的上下文：

```markdown
<!-- FEATURE-CONTEXT:START -->
...feature context required by every section...
<!-- FEATURE-CONTEXT:END -->

<!-- SECTION:S01:START -->
## S01 — Title
...
<!-- SECTION:S01:END -->
```

硬上限再分解之后，层级式 ID 有效：

```markdown
<!-- SECTION:S03.1:START -->
## S03.1 — Smaller descendant
...
<!-- SECTION:S03.1:END -->
```

若 `S03.1` 随后需要再次硬上限拆分，使用诸如 `S03.1.1` 与 `S03.1.2` 的后代。把原始章节视为深度 `0`，并在深度 `3` 以内（例如 `S03.1.1.1`）自主继续。若下一个后代将为深度 `4+`，在 `FEATURE-STATE.md` 与硬上限记录中记录 `BLOCKED_RECURSION_DEPTH`，然后请求人类批准更深层递归或重新规划。

每个活跃章节块必须包含：

```markdown
### 目标
### 行为增量
### 依赖
### 预计范围
### 非目标
### 全局不变量
### 验收标准
### 验证命令
### 发布与恢复
### 延后项
```

对硬上限后代，在 `预计范围` 或元数据中加入谱系，例如：

```markdown
- Lineage: `S03 -> S03.1`
- Replan generation: `1`
- Replaces parent behavior slice: `S03` (parent state: `SPLIT_AFTER_HARD_CAP`)
```

已退役的父章节可以保留在顶层章节索引/历史中，但如果保留会导致相互矛盾的依赖，则不得再作为活跃的可执行章节块。需求/依赖表必须指向活跃后代。

## 2. `PLAN.md`

用途：只针对一个活跃叶子章节的临时执行数据包。

生成的内容包括：

- 来源计划路径与 SHA-256 指纹。
- 提取时间。
- 功能上下文块。
- 恰好一个活跃章节块。

不要附加无关的草稿笔记。把持久的决策放进 `FEATURE-STATE.md`、章节契约或硬上限重规划记录。

只有当活跃章节已被接受、拆分或明确放弃且持久产物已存在后，才删除 `PLAN.md`。

## 3. `FEATURE-STATE.md`

用途：跨代理、上下文重置、评审轮次与硬上限重试的外置状态。

必需的记录：

- 功能 base/当前 head 与执行模式。
- 活跃分支/worktree 与重试分支/worktree。
- 当前状态与下一步动作。
- 章节状态：谱系、base/head、评审轮次、连续干净记录、重规划代数。
- 需求覆盖状态。
- 决策与权限。
- 未决问题与评审位置。
- 已运行/未运行的检查。
- 集成检查点。
- 硬上限事件、备份分支、失败 tip 与后代映射。
- 重置/证据失效事件。
- 延后项与残余风险。

在每次上下文交接之前更新它。

## 4. `{ID}-CONTRACT.md`

用途：一个活跃章节尝试的不可变协议。

必需的记录：

- 章节 ID 与谱系。
- 重规划代数。
- 功能标识符。
- 已冻结的 `section_base` 与依赖 head。
- 目标、行为、非目标与全局不变量。
- 范围与语义边界。
- 验收标准与验证命令。
- 兼容性、迁移、发布、回滚与可观测性。
- 允许延后的工作。
- 重规划/重置触发器。
- 开放的用户拥有的决策；实现之前必须为空。

硬上限拆分使父尝试退役。后代收到根植于相应基点的新契约，而不是原地改写旧契约。

## 5. `{ID}-HANDOFF.md`

用途：给下一个上下文的实现或修复证据。

必需的记录：

- 章节 ID/谱系与评审轮次上下文。
- base/head 或差异指纹。
- 变更的文件与行为。
- 做出的决策及其来源。
- 运行的命令与确切结果。
- 手工/运行时证据。
- 已知限制与延后工作。
- 建议的影响锥边。
- 已授权时的提交 ID。

交接（handoff）是一项待核验的主张，其本身不是证明。

## 6. 评审文件

计数的章节评审命名：

```text
{ID}-SECTION-r01.md
{ID}-SECTION-r02.md
{ID}-SECTION-r03.md
{ID}-SECTION-r04.md
{ID}-SECTION-r05.md
```

可选的非计数修复证据可使用：

```text
{ID}-DELTA-r02-fix01.md
```

最终/集成文件可使用：

```text
FEATURE-INTEGRATION-r01.md
FEATURE-INTEGRATION-DELTA-r01-fix01.md
```

每份计数评审文件应记录：

- 评审模式 `SECTION`。
- 确切的 base/head。
- 契约与功能不变量路径。
- 覆盖与关键路径。
- 带稳定 ID 的新的重大问题。
- 检查/证据。
- 评审者的局部判定。

主编排者单独记录 `review_round` 与 `clean_streak`；个别评审者不决定单次干净评审的接受条件。

## 7. 硬上限重规划文件

命名：

```text
.agent-work/replans/{ID}-g{generation}-HARD-CAP.md
```

必需的记录：

- 失败父章节的 ID/标题与谱系。
- 原始 `section_base`。
- 失败 tip。
- `agent-kit/backup/***` 分支。
- 五份评审文件与被评审的 head。
- 逐轮的新的重大问题/根因。
- 修复提交/检查。
- 反复出现的失败模式。
- `[tier: plan]` 分解者的提示词/上下文摘要。
- 后代 ID 与依赖/需求变更。
- 重试分支/worktree 与新的活跃章节。

使用 `assets/HARD-CAP-REPLAN.template.md`。

## 8. 归档生命周期

最终报告之后：

1. 确保 `FEATURE-STATE.md` 指向实际的最终 head 与最终判定。
2. 确保活跃章节不再依赖临时的 `PLAN.md` 内容。
3. 为每次硬上限拆分保留父/后代谱系。
4. 移除临时的 `PLAN.md`。
5. 把 `PLAN-FULL.md` 移动到 `.agent-work/plans/{YYYYMMDD-HHMM}_FULL.md`。
6. 保留契约、交接、评审文件、重规划文件与备份分支名，除非仓库策略另有规定。

## 9. 辅助脚本命令

```bash
# Validate feature/section headings, markers, hierarchical IDs, references, and dependency DAG
python scripts/section_plan.py validate .agent-work/PLAN-FULL.md

# List sections and titles
python scripts/section_plan.py list .agent-work/PLAN-FULL.md

# Extract an original section
python scripts/section_plan.py extract \
  .agent-work/PLAN-FULL.md S03 --output .agent-work/PLAN.md

# Extract a hard-cap descendant
python scripts/section_plan.py extract \
  .agent-work/PLAN-FULL.md S03.1 --output .agent-work/PLAN.md

# Print SHA-256 fingerprint
python scripts/section_plan.py fingerprint .agent-work/PLAN-FULL.md

# Copy to timestamped archive
python scripts/section_plan.py archive \
  .agent-work/PLAN-FULL.md --dest-dir .agent-work/plans

# Move only after finalization
python scripts/section_plan.py archive \
  .agent-work/PLAN-FULL.md --dest-dir .agent-work/plans --move
```

脚本会拒绝重复 ID、无效的标记/标题、自依赖/未知依赖、依赖环，以及输出/归档覆盖。

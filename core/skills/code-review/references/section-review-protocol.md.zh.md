<!-- 中文翻译版；英文原版为本目录同名 .md 文件。若两者不一致，以英文版为准。 -->

# 章节感知评审协议

当 `$code-review` 被分章节的大型功能工作流调用时使用本协议。它在普通评审协议的基础上扩展，不取代其证据、发现、修复、重置或收敛规则。

## 目录

1. [评审模式](#1-评审模式)
2. [章节评审边界](#2-章节评审边界)
3. [重建章节意图](#3-重建章节意图)
4. [章节发现算法](#4-章节发现算法)
5. [章节特有的发现类别](#5-章节特有的发现类别)
6. [章节验收](#6-章节验收)
7. [章节重置触发器](#7-章节重置触发器)
8. [集成评审重点](#8-集成评审重点)
9. [集成检查点](#9-集成检查点)
10. [评审账本补充字段](#10-评审账本补充字段)
11. [编排者提示词](#11-编排者提示词)

## 1. 评审模式

评审前记录恰好一个主模式。

### `STANDARD`

评审一个普通 PR、提交区间或工作树 diff。使用既有技能工作流。

### `SECTION`

对照冻结的章节契约（section contract）以及它可能影响的功能级不变量，评审一个实现章节（section）。

必需的数据包：

- 功能名称与功能 base。
- 章节 ID。
- 确切的 `section_base..section_head` 或可复现的工作树指纹。
- 功能契约或不变量来源。
- 冻结的章节契约。
- 实现交接与验证证据。
- 声明的依赖与延迟工作。
- 评审输出路径。

结论：

- `section-accepted`
- `section-blocked`
- `insufficient-evidence`

`SECTION` 评审不得宣告整个功能可合并。

### `DELTA`

评审一个修复补丁及其被作废的影响锥。修复前先冻结发现 ID 和验收标准。使用既有的增量验证规则。

结论：

- `delta-verified` — 范围内所有已冻结发现均已关闭，且被作废的影响锥内未引入新的阻塞性缺陷。
- `delta-blocked` — 存在仍处于未决的已冻结发现，或被作废的影响锥内存在新的阻塞性缺陷。
- `reset-required` — 修复实质性改变了基线或语义，需要新的完整发现扫描。
- `insufficient-evidence` — 无法建立必需的闭环证据。

### `INTEGRATION`

评审有界的中途功能检查点，或已接受章节对照原始功能契约的最终组合。记录 `integration_scope: CHECKPOINT | FINAL`。

必需的数据包：

- 功能 base 与当前集成 head。
- 原始目标、非目标、全局不变量和适用的验收标准。
- 需求覆盖矩阵。
- 章节状态与范围内的已接受 head。
- 跨章节契约与集成检查点。
- 延迟工作账本（ledger）。
- 先前评审索引与可用的验证证据。

`CHECKPOINT` 的结论：

- `checkpoint-passed`
- `checkpoint-blocked`
- `checkpoint-insufficient-evidence`

`FINAL` 的结论：

- `mergeable`
- `not mergeable`
- `insufficient evidence`

## 2. 章节评审边界

主要的有界变更是 `section_base..section_head`，而不是整个功能分支。

仅在有需要确立以下事项时才检查范围之外：

- 前置契约的现状。
- 直接调用方/被调用方与共享持有者。
- 公共 API、schema、迁移、权限、状态、并发、发布或运维影响。
- 假设被该章节改变的测试与文档。
- 声明的延迟工作是否使当前中间状态无效。

不要仅仅因为邻近就重开已被接受的前置实现。仅当当前章节作废其契约或证据时才重开。

## 3. 重建章节意图

写下两张独立的卡片。

### 功能卡

- 完整功能目标。
- 非目标。
- 全局不变量。
- 与该章节相关的全功能标准。

### 章节卡

- 确切的行为增量或使能接缝。
- 章节非目标。
- 依赖与前置 head。
- 验收标准。
- 验证命令。
- 兼容性、发布、恢复与延迟工作。

仅当章节契约与仓库/产品权威一致时才将其视为权威。若存在冲突，报告该冲突，而不是悄悄按较弱的文档进行评审。

## 4. 章节发现算法

1. 冻结评审模式、base、head、契约版本和 diff 指纹。
2. 确认章节只改动了声明的范围，或解释每一处扩展。
3. 端到端追踪章节的主要行为。
4. 应用每个被触发的普通评审透镜。
5. 验证章节级验收标准。
6. 挑战该章节触及的功能级不变量。
7. 检查接缝处的前置/消费方契约。
8. 对 `Medium` 或 `Large` 风险，至少测试一条反向、边界或部分失败路径。
9. 验证中间仓库/运行时状态在未来章节之前保持有效。
10. 确认每个延迟项都是显式的、有指派的、可安全推迟的。
11. 将症状归并在稳定的根因发现 ID 之下。

对稳定的章节基线，该完整发现只执行一次。修复之后，计数轮次是针对修复增量及其失效影响锥的 `DELTA` 评审；提供冻结的问题 ID 与已关闭根因 ID（仅 ID 与一行标题），使已关闭的问题不被重新提出。只有重置触发器（第 7 节）生效后才再次执行完整发现。

## 5. 章节特有的发现类别

使用普通的决策类别和严重性。在相关时补充以下常见根因类别：

- `Contract mismatch`（契约不匹配）：实现偏离冻结的章节验收。
- `Feature-invariant violation`（功能不变量违反）：局部正确的行为破坏了全局不变量。
- `Hidden dependency`（隐藏依赖）：章节依赖未言明的未来或前置行为。
- `Invalid intermediate state`（无效中间状态）：在后续章节之前，仓库或运行时无法保持安全。
- `Deferred-work leak`（延迟工作泄漏）：必需行为被推迟却没有负责人或安全边界。
- `Cross-section contract ambiguity`（跨章节契约歧义）：生产方与消费方语义未被冻结。
- `Scope expansion`（范围扩张）：实现吞并了另一章节或无关清理。
- `Evidence gap`（证据缺口）：声称的行为在当前环境中缺少可靠 oracle。

当"功能其余部分尚未实现"已被显式且安全地推迟到指名章节时，不要将其作为发现提交。

## 6. 章节验收

仅当技能的收敛与停止条件在章节范围内成立，且以下章节特有条件也成立时，才返回 `section-accepted`：

- 在未来章节开始之前，中间仓库/运行时状态有效；
- 延迟工作是显式的且有指派；
- 该章节保持了其所触及的功能级不变量。

一个干净的计数轮次即可接受：第 1 轮覆盖完整的完整评审，或修复后 `delta-verified` 的轮次。不要求两次空的全章节评审。

对普通章节，单独的 `FINAL` 扫描是可选的。将其用于风险异常高的章节，或评审者独立性确实能增加证据的场景。该功能以编排工作流的条件性最终门禁收尾。

## 7. 章节重置触发器

当技能的增量再评审与重置规则触发时（公共 API/schema/迁移/权限/状态持有者/并发语义改变、修复重写章节相当部分、范围扩张、base/head 移出被跟踪的修复、证据过期），或当以下情况发生时，执行新的完整 `SECTION` 评审：

- 已冻结的章节验收标准发生实质性变化；
- 前置集成改变了被评审的契约。

记录重置原因并保留先前的发现历史。

## 8. 集成评审重点

`INTEGRATION` 评审以完整功能区间定位，但不应逐行重放每个局部章节。

优先获取章节评审无法独立确立的证据：

- 对照原始目标的完整行为。
- 需求覆盖缺口。
- 跨章节的 API/schema/状态/权限/错误契约。
- 跨章节的顺序、重试、去重、幂等与部分失败。
- 组合后的 UI/API/后台任务流程。
- 迁移顺序与混合版本部署状态。
- 特性开关的开/关行为、发布、回滚与移除。
- 安全、隐私、可观测性、性能、成本与运维就绪。
- 延迟项、临时兼容路径、调试脚手架和分支范围完整性。

在形成独立观点之后再阅读先前章节账本。用它们核对闭环，避免重复已被支持的局部结论。

## 9. 集成检查点

对中途功能检查点，使用带有有界簇的 `INTEGRATION` 模式，而不是全功能合并语义。

检查点结论：

- `checkpoint-passed`
- `checkpoint-blocked`
- `checkpoint-insufficient-evidence`

准确说明组合了哪些章节与契约。当组合后的证据推翻某已接受章节的契约时，检查点可以重开该章节。

## 10. 评审账本补充字段

向 `STATE.md` 或等价的评审文件添加以下字段：

```markdown
- Review mode: STANDARD | SECTION | DELTA | INTEGRATION
- Feature: <name>
- Feature base: <commit>
- Section/checkpoint: <ID or N/A>
- Section base/head: <commits or N/A>
- Contract path/revision: <path/version>
- Feature invariant source: <path>
- Declared dependencies: <IDs/heads>
- Declared deferred work: <items/owners>
```

对章节报告，用章节结论替换最终合并结论，并显式声明：

```text
This verdict is provisional and does not establish whole-feature merge readiness.
```

## 11. 编排者提示词

### 独立章节发现

```text
Review mode: SECTION.
Review section {ID} in {working path} from {section_base} to {section_head}.
Read {feature_contract}, {section_contract}, and {handoff}.
Closed root causes already verified in earlier rounds (IDs and titles only, do not re-raise): {list}.
Use [$code-review]({skill path}/SKILL.md).
Write the review to {output_path}.
Do not repair and do not review the whole feature except for the direct impact cone.
```

### 章节增量验证

```text
Review mode: DELTA.
Verify findings {IDs} for section {ID} in {working path} from {repair_base} to {repair_head}.
Read the frozen findings at {ledger_path} and review only the repair delta plus its invalidated impact cone.
Closed root causes (IDs and titles only, do not re-raise): {list}.
Use [$code-review]({skill path}/SKILL.md).
Write the result to {output_path}.
```

### 最终功能集成评审

```text
Review mode: INTEGRATION.
Review feature {name} in {working path} from {feature_base} to {feature_head}.
Read {feature_contract}, {feature_state}, section artifacts, and the review index.
Use [$code-review]({skill path}/SKILL.md).
Focus on full acceptance and cross-section interactions; do not mechanically replay every accepted local line.
Write the review to {output_path}.
```

<!-- 中文翻译版；英文原版为本目录同名 .md 文件。若两者不一致，以英文版为准。 -->

# 审计循环协议（Audit Loop Protocol）

使用本协议来运行持续积累可信覆盖、针对变化风险、并在修复后收敛的周期审计。它用持久状态、显式失效、轮换深度与场景验证，取代反复的全仓库重扫。

## 目录

1. [核心模型](#core-model)
2. [持久状态](#persistent-state)
3. [基线审计](#baseline-audit)
4. [周期审计](#periodic-audit)
5. [范围分配](#scope-allocation)
6. [覆盖新鲜度与失效](#coverage-freshness-and-invalidation)
7. [发现与证据](#discovery-and-evidence)
8. [决策与修复](#decision-and-remediation)
9. [定向复审](#targeted-re-audit)
10. [全面基线重置](#full-baseline-reset)
11. [收敛与预算](#convergence-and-budget)
12. [黄金原则与技术债控制](#golden-principles-and-debt-control)
13. [编排器提示词](#orchestrator-prompts)
14. [参考伪代码](#reference-pseudocode)

## 核心模型

周期审计不是"把每个文件再看一遍"。它是一个跨时间的风险控制过程：

```text
profile + system map + change history + incidents + coverage freshness + open debt
    -> scope selection
    -> evidence-backed discovery
    -> findings and gaps
    -> decisions/remediation
    -> targeted re-audit
    -> durable coverage and guardrails
```

保持以下区分清晰：

- `Baseline audit`（基线审计）：建立可信赖的系统/风险/覆盖状态。
- `Periodic audit`（周期审计）：更新已变更、已失效、关键与轮换区域。
- `Targeted re-audit`（定向复审）：验证修复增量及其依赖场景。
- `Reset baseline`（重置基线）：在重大系统/风险变迁后重建广泛结论。

提交数量可以触发一次周期审计，但不能单独决定范围。三十个小的文档提交和一次授权重设计所承载的风险并不相同。

## 持久状态

维护四份持久控制工件。

### 审计画像（profile）

定义：

- 系统边界与所有者。
- 关键工作流与核心资产。
- 风险/影响分类与容忍度。
- 质量属性优先级。
- 必需的覆盖与证据。
- 安全、可靠性、供应链与 agent 基线。
- 抽样与严重级别校准。

画像只在系统或风险策略变化时改变，不是每次运行都改。

### 系统地图

绘制：

- 组件/域与所有者。
- 接口/契约与依赖方向。
- 数据存储/事件/队列与状态归属。
- 信任边界与特权操作。
- 部署/发布/运维拓扑。
- Agent/工具控制平面。
- 场景路径与依赖关系。

地图使有界失效成为可能。没有它，每次变更看起来都需要全仓库重扫。

### 覆盖账本（coverage ledger）

对每个区域/场景记录：

- 关键度与所需深度。
- 最近评审的提交/日期/环境。
- 证据与已知缺口。
- 依赖与失效触发器。
- `Fresh`、`Stale`、`Invalidated` 或 `Unknown` 状态。
- 下次轮换原因。

### 发现/技术债账本（findings ledger）

持久保存：

- 未关闭与已关闭的根因发现。
- 带负责人、上限与触发条件的已接受风险与技术债。
- 反复出现的问题类别。
- 黄金原则候选（golden principle candidate）及其执行状态。
- 重开证据。

不要让单次运行的报告取代这些持久账本。

## 基线审计

使用基线审计建立可信起点。

### 第 1 步：批准或起草画像

解决或显式假设：

- 关键工作流与资产。
- 风险容忍度与影响等级。
- 安全/可靠性/控制基线。
- 必需证据。
- 排除项与抽样边界。

仅当未解决的决策会实质性改变优先级或可接受行为时才阻塞。否则以清楚标注的假设继续。

### 第 2 步：构建系统地图

调查仓库结构、入口点、数据流、信任边界、部署、CI/CD、运维与 agent 工具链。不要在绘图阶段深入审计每个文件。

### 第 3 步：划分区域

分配：

- 关键度：`Critical`、`High`、`Medium`、`Low`。
- 变更/变动程度。
- 证据可得性。
- 所需审计深度。
- 依赖扇入/扇出。
- 初始新鲜度：通常为 `Unknown`。

### 第 4 步：定义场景组合

选择关键场景，例如：

- 认证与授权。
- 租户/数据隔离。
- 核心事务/工作流正确性。
- 迁移与滚动部署兼容性。
- 后台任务重试/幂等。
- 依赖中断与降级模式。
- 备份/恢复与事故恢复。
- 发布/回滚。
- 适用时的 agent 提示注入/工具滥用。

### 第 5 步：按风险切片审计

审计关键场景与代表性子系统切片。每个单元完成后立即更新覆盖。基线可以跨多次运行；将未评审区域标记为 `Unknown`，绝不静默补全。

### 第 6 步：公布基线边界

说明哪些是新鲜的、部分的、未知的、排除的或被阻塞的。除非画像定义并证据证明了该覆盖水平，否则不要宣称仓库"已全面审计"。

## 周期审计

以上一份账本为起点。

### 第 1 步：校准现实

- 检查当前 head、tag/发布、状态，以及自上次运行以来的变更区间。
- 确认持久工件指向当前的文件、组件、工作流与所有者。
- 阅读自上次运行以来的事故/缺陷/运维证据。
- 识别重大的依赖、平台、模型、harness 或工具链变更。

### 第 2 步：计算已变更与已失效区域

按语义而非文件数量分类变更：

- 行为/领域。
- 数据/schema/迁移。
- 认证/权限/隐私。
- 并发/任务/事件。
- 发布/配置/CI/运维。
- 依赖/构建/供应链。
- 架构/归属。
- Agent/harness/工具链。
- 测试/评测/校验。
- 文档/唯一事实来源。

沿系统地图的边，只使那些假设可能改变的结论失效。

### 第 3 步：加入常开关键区域

即使没有直接代码变更，也纳入画像规定的关键面，当：

- 其证据已过期。
- 它们依赖已变更的基础设施或契约。
- 它们承载需要周期性确认的严重影响。
- 事故或遥测显示漂移。

### 第 4 步：加入轮换深切片

选择近期未被审计的区域，优先：

- 高关键度。
- 高变动或高复杂度。
- 薄弱的测试/可观测性。
- 广泛扇入/扇出。
- 接近触发条件的已接受技术债。
- 归属变更。
- agent 生成的增长或重复模式。

轮换防止看似稳定、未被触碰的风险无限期地游离在审计之外。

### 第 5 步：加入事故与发现跟进

纳入：

- 逃逸缺陷。
- 安全告警与滥用报告。
- 不稳定或被抑制的检查。
- 运维琐务与人工修复。
- 被重开的发现。
- 到达评审日期/阈值的已接受风险项。
- 需要补证据的黄金原则候选。

### 第 6 步：写入显式范围

在深入发现之前，将选定区域、理由、场景、证据目标、排除项与资源上限写入本次运行的 `SCOPE.md`。

## 范围分配

普通周期审计的一个有用起点启发式：

- **35%** 已变更/高变动区域与已失效的依赖锥。
- **25%** 常开关键场景。
- **25%** 轮换深切片。
- **15%** 事故、未关闭发现、技术债与证据缺口。

这是规划启发式，不是标准或评分。当风险需要时可以覆盖它。示例：

- 一次授权重设计可能占用几乎整个周期。
- 一条安静但关键的恢复路径值得超过轮换份额的分配。
- 一次重大事故可能把该运行变成定向取证审计。

按风险与所需证据分配预算，而不是按相等的文件数。

## 覆盖新鲜度与失效

### Fresh（新鲜）

仅当以下条件满足时标记 `Fresh`：

- 所需范围已对照记录的仓库/环境检查。
- 存在所需的场景或控制证据。
- 已知缺口低于画像阈值。
- 没有生效的失效触发器。

### Stale（过期）

当置信度衰减但没有直接矛盾时标记 `Stale`：

- 评审时间超过画像节奏。
- 附近（但不在此区域内）发生了显著变动。
- 依赖/运行时版本变化但未证明语义影响。
- 运行时/运维证据过旧。
- 归属或文档发生变化。

### Invalidated（已失效）

当某次变更或事件直接打破既往证明假设时标记 `Invalidated`：

- 契约/schema/接口变化。
- 调用方/被调方或依赖行为变化。
- 认证/数据/信任边界变化。
- 部署拓扑或配置变化。
- 新事故推翻了预期行为。
- 修复重写了被评审的路径。
- 唯一事实来源或生成产物变得不一致。

### Unknown（未知）

当证据不存在或无法对照时使用 `Unknown`。

### 失效图

对每个覆盖项存储显式依赖与触发器。沿以下方向扩展失效：

- API/事件/schema 的消费者与生产者。
- 数据读/写方、缓存与迁移。
- 状态转换、任务、队列、重试与锁。
- 权限/策略/租户边界。
- 配置、特性开关、部署、回滚与可观测性。
- 编码了假设的测试/评测/文档。
- 在该区域上运作的 agent 提示词/工具/权限。

当变更节点无法影响场景所需的响应或证据时停止。记录边界与理由。

避免虚假精度。不要把状态压成单一百分比而隐藏关键的未知项。

## 发现与证据

### 将候选生成与修复分离

在每个划定的区域内：

1. 说明质量属性与场景。
2. 通过相互独立的透镜生成候选失败模式。
3. 追踪可达性与受影响的不变量。
4. 尝试证伪每个候选。
5. 运行定向测试、扫描、运行时检查或实验。
6. 按根因去重。
7. 在进入下一区域前更新证据与覆盖。

在同一区域的广泛发现仍在进行时不要修复；过早的修复会抹除证据、带偏评审者，并在无追踪的情况下扩大范围。

### 证据组合

使用可行的最强组合：

- 当前代码/配置与数据流追踪。
- 单元/集成/端到端测试。
- 属性、状态机、差分、模糊、负载、混沌、迁移、回滚或恢复检查。
- 静态/类型/安全/依赖/密钥/策略扫描。
- 运行时日志、指标、追踪、仪表盘、告警与事故记录。
- 部署/构建/来源证明。
- 运维/用户工作流的人工验证。
- 权威画像、契约、ADR 与生成来源。

一次干净的自动化扫描只是一层防线，不是审计结论。

### 区域结果

每个划定区域以以下内容收尾：

- 覆盖状态与证据。
- 发现或 `No Action`。
- 缺口/假设。
- 失效触发器。
- 下次轮换原因。

## 决策与修复

划分发现：

- `Needs Decision`：风险容忍度、业务语义、控制基线、架构权衡、兼容性或运维行为需要授权。
- `Agent-Fixable`：预期的控制与结果已明确。
- `External Blocker`：证据/环境/负责人不可得。

只询问影响修复或风险排序的决策。将答复持久记录。

### 修复波次选择

当发现共享以下特征时分批：

- 同一根因或策略边界。
- 同一部署/迁移顺序。
- 同一验证策略。
- 有界的依赖锥。

避免巨大的"清偿全部技术债"波次。它们抹除归因，并制造新的未审计架构。

### 修复约束

- 冻结发现 ID 与验收标准。
- 在安全前提下保留原始失败的证据。
- 优先根因控制而非局部补丁。
- 在可能复发处添加可执行护栏。
- 不得为获得关闭而削弱测试、扫描、权限、可观测性或回滚。
- 记录变更、检查、缺口与契约扩张。

## 定向复审

在一个修复波次之后：

1. 从上一个被审计的 head 到修复后 head 做 diff。
2. 映射变更的组件、契约、数据、权限、运维与控制。
3. 沿失效图扩展。
4. 重跑原始的失败/恢复/滥用场景。
5. 验证每条冻结的验收标准。
6. 检查新分支、依赖、状态、回退路径与运维路径。
7. 只更新受影响的覆盖项。
8. 若根因仍在，重开同一发现 ID。
9. 仅对不同的根因创建新 ID。

不要在修复验证轮中重复所有未受影响模块或轮换新切片。保持修复验证可归因。

## 全面基线重置

当定向失效无法可信地界定变更范围时重置。

触发器包括：

- 重大架构/运行时/平台/语言/框架迁移。
- 身份、授权、租户、隐私或数据模型重设计。
- 新的受监管范围、核心资产、特权工作流或风险偏好。
- 新的部署拓扑、构建/发布链、关键依赖或工件模型。
- 新的 agent 平台、自主级别、MCP/工具信任边界或模型/harness 控制平面。
- 重大安全/数据/可靠性事故。
- 改变多个系统不变量的广泛修复或迁移。
- 账本缺失/损坏，或系统地图不再描述现实。

### 重置流程

- 归档但不抹除历史发现/证据。
- 重新批准或更新画像。
- 重建系统地图。
- 视情况将大范围覆盖标记为 `Unknown` 或 `Invalidated`。
- 携带仍然相关的未关闭发现与已接受风险。
- 定义新的基线计划与场景组合。

## 收敛与预算

### 审计运行的完成

当以下条件满足时完成运行：

- 每个划定区域有记录的结果。
- 每条发现有证据支撑，或被显式标注为假设/缺口。
- 必需场景已运行，或带剩余风险地被阻塞。
- 持久账本是最新的。
- 本次运行中授权的修复已验证，或保持公开受阻状态。
- 报告说明覆盖边界与下一步优先级。

一次审计运行可以带着未关闭发现完成。`Completed` 表示计划中的审计工作完成，不是系统无风险。

### 修复循环预算

默认：

- 对选定的审计范围执行一轮发现波次。
- 同一次运行中最多三轮修复波次。
- 对已修复的关键发现执行一次独立的或阶段分离的最终验证。
- 修复波次硬上限为五轮。

到达硬上限时，阻塞修复并诊断：

- 画像/业务决策缺失。
- oracle 薄弱或缺失。
- 架构冲突。
- 修复震荡。
- 范围爆炸。
- 仓库/环境不稳定。
- 生产/第三方证据不可访问。
- agent/harness 反复失败。

不要只回复"继续？"。给出有界的选项与后果。

### 进展检验

一个波次只有在做到以下之一时才算有进展：

- 以证据关闭一条发现。
- 证伪一个候选并消除不确定性。
- 以证据新增一个根因。
- 使覆盖变 Fresh。
- 把复发转化为持久控制。
- 解决一个已到期的技术债触发条件。

重复扫描、重述摘要与重复发现都不算进展。

## 黄金原则与技术债控制

### 黄金原则候选（golden principle candidate）

当一类复发问题具备以下条件时将其提升：

- 反复出现的证据，或一次严重的系统性事件。
- 清晰、持久的不变量。
- 可机械执行或可明确传授的规则。
- 可接受的误报/维护成本。
- 负责人及更新/退役路径。

记录：

- 问题类别与出现记录。
- 不变量。
- 执行选项。
- 预期预防的失败。
- 误报/逃逸风险。
- 负责人。
- 推广与验证。

可选执行方式：

- 静态/结构/策略 lint。
- schema/类型校验器。
- 共享边界抽象。
- 回归/属性/集成/恢复测试。
- 生成器/模板更新。
- CI/发布控制。
- 链接到权威文档的简短仓库指令。

### 技术债记录

每条已接受的技术债务必须包含：

- 负责人。
- 为何当前可接受。
- 安全上限或有界范围。
- 可观察的 revisit 触发条件。
- 适当时的截止日期/节奏。
- 缓解与监控。
- 预期的移除/修复路径。

"以后再说"不是技术债计划。

### 持续清理

优先窄而频繁的清理任务，而非罕见的大规模重构。用审计证据选择定向工作：

- 反复出现的重复模式。
- 陈旧的兼容路径。
- 死配置/开关。
- 文档/唯一事实来源漂移。
- 依赖与权限蔓延。
- 架构适应度违规。
- agent 生成的膨胀热点。

保持每次清理可评审、可回滚，并被独立验证。

## 编排器提示词

### 独立审计发现

```text
Audit {working path}, [code-audit]({skill path}/SKILL.md)
```

除非用户要求定向审计，否则独立的发现提示词中不要包含既往疑似发现。

### 修复 agent

```text
Remediate only accepted Agent-Fixable audit findings {IDs} in {working path}.
Read {FINDINGS.md} and the current run scope/evidence.
Preserve frozen acceptance criteria. Do not commit, push, deploy, or perform unrelated cleanup.
Record the exact remediation delta and verification evidence for every ID.
```

### 定向复审者

```text
Re-audit the remediation from {previous head} to {current head} for findings {IDs}.
Review the remediation delta, invalidated system-map cones, and original scenarios only.
Reopen findings whose acceptance criteria are not proven. Update persistent coverage with current evidence.
```

### 全新的最终验证者

```text
Perform a fresh verification of the remediated critical audit findings in {working path} using the approved audit profile.
Start from current code/configuration, system scenarios, and raw remediation diff. Inspect independently before reading prior rationalizations, then verify ledger closure evidence.
```

## 参考伪代码

```text
profile = load_or_draft_profile()
map = load_or_build_system_map()
coverage = load_or_initialize_coverage()
findings = load_or_initialize_findings()
repo = reconcile_current_repository()

if broad_reset_trigger(profile, map, coverage, repo):
    mode = BASELINE
    archive_history_without_erasing_findings()
    profile = reapprove_profile(profile, repo)
    map = rebuild_system_map(repo)
    coverage = invalidate_broad_coverage(coverage)
else:
    mode = PERIODIC
    map = refresh_changed_system_map_edges(map, repo)

scope = select_scope(
    always_on=profile.required_critical_coverage,
    changed=changes_since_last_run(repo),
    invalidated=propagate_invalidation(map, coverage, repo),
    rotating=due_rotating_slices(coverage),
    incidents=recent_incidents_and_failures(),
    debt=open_findings_and_due_debt(findings)
)
write_SCOPE(scope)

for area in scope:
    scenarios = define_scenarios(area, profile, map)
    candidates = generate_hypotheses(area, scenarios)
    results = validate_falsify_and_deduplicate(candidates)
    append_EVIDENCE(area, results)
    update_coverage(area, results, repo)
    update_findings(results)

partition findings into decisions, fixable, blockers

if decisions block remediation:
    mark_remediation(BLOCKED, "authority decision required")
    ask_required_decisions(decisions)

if remediation_authorized:
    repair_waves = 0
    while accepted_fixable_findings_exist():
        if repair_waves >= 5:
            block_with_convergence_diagnosis()
            break

        wave = choose_smallest_coherent_wave()
        previous_head = current_head()
        remediate(wave)
        repair_waves += 1
        delta = diff(previous_head, current_head())

        if broad_reset_triggered_by(delta):
            record_reset()
            mode = BASELINE
            break

        invalidated = propagate_delta_invalidation(map, coverage, delta)
        verification = targeted_reaudit(wave, delta, invalidated)
        update_findings_and_coverage(verification)

        if not round_made_progress(verification):
            diagnose_and_block_or_change_control_strategy()

finalize_persistent_ledgers()
write_chinese_REPORT(
    mode, profile, scope, evidence, findings,
    coverage_updates, gaps, repairs, next_priorities
)
delete_CURRENT()
mark_audit_run(COMPLETED)
```

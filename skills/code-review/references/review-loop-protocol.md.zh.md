<!-- 中文翻译版；英文原版为本目录同名 .md 文件。若两者不一致，以英文版为准。 -->

# 评审循环协议

当评审可能修复发现（finding）并进行多轮迭代时使用本协议。其目的在于最大化首轮发现的产出，同时让后续各轮保持增量式、证据驱动并最终收敛。

## 目录

1. [核心规则](#核心规则)
2. [状态机](#状态机)
3. [角色](#角色)
4. [完整发现算法](#完整发现算法)
5. [决策门](#决策门)
6. [修复波次](#修复波次)
7. [增量验证](#增量验证)
8. [影响锥扩展](#影响锥扩展)
9. [全量重置触发器](#全量重置触发器)
10. [全新最终验证](#全新最终验证)
11. [收敛与预算](#收敛与预算)
12. [单智能体回退方案](#单智能体回退方案)
13. [编排者提示词](#编排者提示词)
14. [参考伪代码](#参考伪代码)

## 核心规则

对每个稳定基线（baseline）只执行恰好一次完整发现扫描。稳定基线可以是普通变更、一个冻结的实现章节（section），或最终集成后的功能区间。修复之后，只评审：

- 修复增量（repair delta）。
- 被该增量作废的语义与运维影响锥。
- 证据已发生变化的既往评审结论。

仅在显式重置触发器（reset trigger）之后才开始新一轮完整发现扫描。绝不把"再跑一遍同样的完整评审"当作常规迭代原语。

将四项活动分开：

1. 生成失效假设。
2. 验证或证伪假设。
3. 修复已接受的发现。
4. 验证修复后的状态。

把它们混在一场不加区分的对话中会助长锚定、自我辩护、遗忘发现和重复扫描。

## 状态机

```text
INITIALIZE
  -> FULL_DISCOVERY
  -> DECISION_GATE
       -> BLOCKED_DECISION       when business semantics are unresolved
       -> REPAIR_WAVE            when authorized fixable findings exist
       -> FINAL_FRESH_VERIFY      when no repair is required
  -> DELTA_VERIFY
       -> REPAIR_WAVE            when accepted findings remain
       -> FULL_DISCOVERY          only after RESET
       -> FINAL_FRESH_VERIFY      when closure criteria are met
  -> COMPLETE | BLOCKED
```

对大型或多轮评审，将状态持久化到 `STATE.md` 和 `FINDINGS.md`。

使用以下轮次模式：

- `FULL`：针对稳定的普通 base/head 进行完整发现。
- `SECTION`：针对一个冻结的章节 base/head 与契约进行完整发现。
- `DELTA`：修复增量加上被作废的影响锥。
- `RESET`：因基线或语义发生实质性变化而进行新的完整发现。
- `INTEGRATION`：跨章节或全功能组合评审。
- `FINAL`：在能够提供独立证据时进行的全新上下文对抗性验证。

## 角色

优先使用不同的角色，而不必是不同的模型：

### 发现评审者

- 接收原始仓库、有界变更和普通技能提示词。
- 重建意图并在相互独立的透镜下生成候选。
- 在发现阶段不修改代码。
- 以稳定 ID 冻结有证据支撑的发现。

### 决策所有者

- 裁定产品语义、兼容性策略、风险接受、UX 意图和其他属于权威层面的选择。
- 不需要裁决确定性的实现细节。

### 修复智能体

- 只接收已接受的 `Agent-Fixable`（智能体可修复）ID、验收标准和相关证据。
- 完成最小连贯修复。
- 精确记录改动了什么、运行了哪些检查。
- 不能凭断言关闭发现。

### 验证评审者

- 评审修复增量和影响锥。
- 当验收标准未满足时重开发现。
- 仅为真正不同的根因创建新的稳定 ID。

### 最终全新验证者

- 从当前代码、意图、不变量和原始 diff 出发。
- 在独立检查之前避免接触先前评审者的合理化解释。
- 检查最高风险的工作流和闭环证据。

## 完整发现算法

### 1. 冻结基线

记录：

- 仓库路径。
- base 与 head 提交，或确切的本地 diff 命令。
- diff 指纹，例如提交 ID 加上补丁哈希。
- worktree 状态。
- 评审深度和被触发的风险透镜。

不要在基线未指定或仍在移动的情况下开始多轮循环。

### 2. 构建意图与不变量卡

写下：

- 一句话目标。
- 明确的非目标。
- 用户/业务不变量。
- 安全/数据/可靠性不变量。
- 兼容性与发布假设。
- 需要验证的声明。

未决的不变量应归为 `Needs Decision`（需要决策）或显式的证据缺口，而不是被发明成假设。

### 3. 映射变更图

映射变更节点与相关边：

- 入口点与外部接口。
- 调用方与被调用方。
- 状态持有者与事件流。
- schema、迁移、缓存、队列和文件。
- 认证与权限门禁。
- 配置、特性开关、CI、部署和回滚。
- 测试、文档、日志、指标和告警。

### 4. 按透镜生成候选

对 `review-coverage.md` 中每个被触发的透镜：

- 显式进入该评审思维模式。
- 生成具体的失效假设。
- 在不编辑的前提下记录候选。
- 使用不同的场景族：边界值、非法迁移、部分失败、重试、并发、恶意输入、混合版本、操作员失误和回滚。

不要让一个早期看似合理的发现吞噬其余评审。先完成所有强制透镜的候选生成。

### 5. 验证与证伪

对每个候选：

- 追踪可达性。
- 识别被违反的不变量。
- 搜索能反驳它的守卫或契约。
- 在可行处运行定向检查。
- 记录支持性与反驳性证据。
- 丢弃无法坐实的投机性低严重度候选。

### 6. 根因去重

按"修复它能一并关闭这些实例"的最小共同原因对发现分组。将位置作为出现（occurrence）附上，而不是每行提一条意见。

示例：

- 四条路由都缺少对象级授权 → 一个根因，四次出现。
- 共享序列化器在六个 API 中输出错误时间戳 → 一个根因。
- 三条互不相关的错误路径各自泄漏不同机密 → 分列为独立发现，除非是同一个日志抽象导致全部三者。

### 7. 冻结发现

分配稳定 ID（stable ID）。冻结：

- 根因。
- 触发条件。
- 影响。
- 证据。
- 严重性。
- 决策类别。
- 验收标准。
- 初始受影响范围。

修复可以补充证据或受影响的出现，但不得悄悄削弱原始验收标准。

## 决策门

将未决发现划分为：

- `Needs Decision`（需要决策）。
- `Agent-Fixable`（智能体可修复）。
- `External Blocker`（外部阻塞）。

当某项决策会改变安全的实现方向时，先阻塞再修复。提出一个紧凑的问题，包含：

- 发现 ID。
- 相互竞争的语义或风险选项。
- 每个选项的后果。
- 推荐默认项（当仓库证据支持时）。

不要让用户审批可以从既有契约推导出的普通实现细节。

一项决策是持久证据。将其记录到账本（ledger），并在合适时记录到仓库本地的产品/架构文档，以免后续智能体重新打开同一处歧义。

## 修复波次

仅当已接受的发现共享连贯的变更边界并能被一起验证时，才将它们归入同一波次。

### 修复约束

- 只修复已冻结的 ID。
- 避免投机性重构。
- 保留原始 base 以供对照。
- 增加或强化最小有用的回归 oracle。
- 优先采用根因修复而非反复打局部补丁。
- 当已接受的语义使旧回退或兼容代码不再必要时，将其移除。
- 不得为了让结果变绿而削弱测试、CI、扫描器、类型、权限或日志。

### 修复产出

对每个 ID，记录：

- 变更的文件与符号。
- 修复说明。
- 新增或变更的测试。
- 命令与输出。
- 已知缺口。
- 该修复是否改变了任何契约或扩大了范围。

改变了契约的修复必须先对照重置规则评估，再进行增量验证。

## 增量验证

从上一个已验证 head 到新 head 构造修复补丁。评审该补丁，而不是重新评审整个原始 PR。

### 验证每个已修复的发现

- 复现或推演原始触发条件。
- 确认验收标准。
- 确认被处理的是根因，而不只是一处出现。
- 检查旁路与同级路径。
- 运行定向回归 oracle。
- 检查修复没有削弱其他不变量。

### 仅在被作废的影响锥内搜索新缺陷

- 评审由修复引入的新分支、回退路径、状态、依赖、权限和错误行为。
- 仅当修复作废了相邻未变更代码的假设时才检查它。
- 不要为了寻求随机变化而重开此前已验证的未受影响区域。

### 轮次结果

记录：

- 已关闭、已重开或仍处于未决的发现。
- 新的根因发现。
- 被作废并重新验证过的覆盖结论。
- 已运行的检查。
- 是否触发了重置触发器。

## 影响锥扩展

从修复增量中的每个变更文件、hunk、符号、schema、配置键和工作流出发。仅沿语义相关的边扩展。

### 代码边

- 直接调用方与被调用方。
- 被变更接口的实现。
- 覆写与分发注册。
- 共享的校验器、序列化器、错误映射器和策略门禁。
- 被变更常量、类型和导出 API 的导入方。

### 数据边

- 被变更字段/表/文件/缓存键/事件的读方与写方。
- 迁移与混合版本兼容性。
- 索引、约束、保留期和恢复路径。

### 状态/并发边

- 被变更事件的生产者/消费者。
- 锁、事务、队列、重试、定时器、取消和去重。
- 谓词或副作用被改变的状态迁移。

### 安全边

- 被变更操作前后 的认证与授权门禁。
- 租户/用户范围的传播。
- 信任边界验证与输出处理。
- 令牌、机密、网络、文件系统、命令或工具权限。

### 运维边

- 配置/环境/特性开关。
- 部署与回滚顺序。
- 可观测性与告警。
- 容量、配额和第三方故障处理。

### 证据边

- 编码了旧行为的测试与 fixture。
- 作为事实来源使用的文档、计划、生成的 schema 和 runbook。
- 其证明引用了被变更代码的既往发现结论。

当某条边不可能改变观测行为或作废先前证据时停止扩展。记录该边界，以便后续评审者可以挑战它。

## 全量重置触发器

当任一条件成立时，重置基线并执行新的完整发现：

1. 公共 API、持久化 schema、迁移、事件契约或兼容性承诺发生实质性变化。
2. 认证、授权、租户隔离、数据分级、机密处理或特权工具的方向发生改变。
3. 并发、事务、幂等、破坏性动作、队列或重试语义发生实质性变化。
4. 部署拓扑、发布顺序、回滚、环境、CI 权限或特性开关策略发生实质性变化。
5. 归属或架构方向发生改变，例如引入新的状态持有者或替换共享层。
6. 修复波次扩展到原始目标之外，或重写了行为的相当部分。
7. base 分支或 head 在被追踪的修复补丁之外发生变化。
8. 账本无法与仓库现状对账。
9. 新证据推翻了原始意图或不变量模型。
10. 最终验证者发现可能影响先前大范围已评审区域的新系统性根因类别。

可以使用可配置的扰动阈值（例如行为 diff 被重写 20–30%）作为警告信号，而不是自动证明。语义变化优先于数值阈值。

## 全新最终验证

在可能时使用全新上下文（fresh context）。

### 输入顺序

1. 当前仓库和原始有界 diff。
2. 权威意图、不变量和已接受的决策。
3. 必需检查与高风险工作流。
4. 仅在独立检查之后才阅读先前账本。

### 必问问题

- 当前代码是否做了被要求的事并保持不变量？
- 是否存在先前评审遗漏的可达高影响失效？
- 修复是否引入了不同的根因？
- 安全/数据/发布声明是否有证据支撑？
- 闭环证据是否确实对应当前 head？
- 剩余风险是否被诚实地界定？

最终验证者不应重做每一行低风险代码。它应挑战最高风险的结论、修复影响锥，以及先前智能体有动机宣称完成的地方。

## 收敛与预算

### 常规预算

- 一轮 `FULL` 发现。
- 常规条件下至多三个修复波次。
- 对大型普通评审或最终集成门禁，执行一次 `FINAL` 全新验证。对无修复的章节，它是可选的；章节修复之后，一次成功的独立 `DELTA` 验证通常已足够，除非风险或重置触发器支持更多验证。

### 硬上限

默认以五个修复波次为硬上限。到达上限时，阻塞并诊断收敛失败，而不是询问泛泛的"要继续吗？"。

对阻塞项分类：

- `Specification gap`（规格缺口）：预期行为缺乏权威来源。
- `Weak oracle`（弱 oracle）：测试/检查无法区分正确与貌似正确。
- `Architecture conflict`（架构冲突）：局部修复反复违反另一边界。
- `Oscillation`（震荡）：修复在互不兼容的行为之间摇摆。
- `Scope explosion`（范围爆炸）：每次修复都扩大影响锥。
- `Unstable base`（基线不稳定）：无关变更使证据失效。
- `Environment gap`（环境缺口）：无法运行所需行为。
- `Model/harness limitation`（模型/harness 限制）：同一智能体在明确证据面前反复重复已知模式。

提供有界选择：裁定语义、增加 oracle、拆分变更、重新设计边界、恢复稳定基线、引入专家、接受已记录的剩余风险，或显式延长预算。

### 进展判据

只有当一轮至少做到以下之一时才算有进展：

- 以证据关闭一个已接受的发现。
- 证明某候选为假并消除不确定性。
- 新增一个真正有证据支撑的根因。
- 关闭一个强制覆盖缺口。
- 把一个反复出现的失效转化为持久的测试、lint、规则或已记录的不变量。

反复重述症状、重排报告格式或重跑同一扫描都不算进展。

### 重复失败类别

当同一问题类别在一次变更中出现两次或跨变更反复出现时，提出 harness 改进：

- 回归测试或性质测试。
- 静态或结构化 lint。
- 共享校验器或策略门禁。
- 生成器/模板修改。
- 仓库规则或架构文档。
- CI 强制。

不要把每个偏好都变成规则。只提升具有重复证据、清晰不变量、低误报成本和明确负责人的规则。

## 单智能体回退方案

当只有一个智能体可用时，模拟角色分离：

1. 不做编辑地完成发现。
2. 持久化冻结的发现与覆盖。
3. 结束发现阶段，只重读已接受的 ID。
4. 修复最小波次。
5. 从冻结的 head 生成干净的修复 diff。
6. 从 diff 而非记忆重建影响锥。
7. 对每个 ID 尝试证伪其闭环。
8. 以不同的评审框架和输入顺序执行最终扫描。

该智能体不得因为"我修好了"而关闭发现。只有当原始触发条件不再可达，或不变量现已强制执行并被验证时，才能关闭它。

## 编排者提示词

### 独立发现

对 `SECTION` 和 `INTEGRATION` 评审数据包，还需遵循 `section-review-protocol.md`。

```text
Review {working path}, [$code-review]({skill path}/SKILL.md)
```

保持该提示词最小化以保留独立差异性。评审者自行收集仓库上下文。

### 授权修复

```text
Repair only the accepted Agent-Fixable findings {IDs} in {working path}.
Read {ledger path}. Preserve every frozen acceptance criterion.
Do not commit, push, update the PR, or perform unrelated cleanup.
Record the repair diff and verification evidence for each ID.
```

### 增量验证者

```text
Verify the repair wave from {previous head} to {current head} in {working path}.
Read the frozen findings {IDs} and review only the repair delta plus its invalidated impact cone.
Reopen any finding whose acceptance criterion is not proven. Create new IDs only for distinct root causes.
```

### 全新最终验证者

```text
Perform a fresh merge-readiness verification of {bounded change} in {working path} using [$code-review]({skill path}/SKILL.md).
Start from the current repository, authoritative intent, and invariants. Independently inspect the highest-risk paths before reading prior review rationalizations. Verify current closure evidence and report any new material root-cause class.
```

## 参考伪代码

```text
state = initialize_baseline_and_ledger()
mode = FULL
repair_waves = 0

while true:
    if mode in {FULL, RESET}:
        candidates = generate_candidates_across_triggered_lenses(state)
        findings = validate_falsify_and_deduplicate(candidates)
        freeze_findings(findings, state)

    decisions, fixable, blockers = partition_open_findings(state)

    if decisions block a safe repair:
        mark_goal(BLOCKED, reason="business semantics")
        ask_only_required_decisions(decisions)
        break

    if blockers prevent required evidence:
        mark_goal(BLOCKED, reason="external evidence")
        report_blockers_and_residual_risk(blockers)
        break

    if fixable is empty:
        final_result = fresh_final_verify(state)
        if final_result.has_new_material_root_cause:
            add_findings(final_result.findings, state)
            mode = RESET if final_result.is_systemic else DELTA
            continue
        if stop_conditions_hold(state):
            mark_goal(COMPLETED)
        else:
            mark_goal(BLOCKED, reason="insufficient evidence")
        break

    if repair_waves >= 5:
        mark_goal(BLOCKED, reason=diagnose_non_convergence(state))
        ask_for_bounded_resolution_choice()
        break

    wave = select_smallest_coherent_repair_wave(fixable)
    frozen_head = current_head()
    repair(wave)
    repair_waves += 1

    delta = diff(frozen_head, current_head())
    if reset_triggered(delta, state):
        record_reset_reason(state)
        state = rebaseline_preserving_finding_history(state)
        mode = RESET
        continue

    cone = expand_invalidated_impact_cone(delta, state)
    delta_result = verify_repairs_and_cone(wave, delta, cone)
    update_findings_coverage_and_evidence(delta_result, state)
    mode = DELTA
```

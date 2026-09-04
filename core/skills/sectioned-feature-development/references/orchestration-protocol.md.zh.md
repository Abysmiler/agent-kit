<!-- 中文翻译版；英文原版为本目录同名 .md 文件。若两者不一致，以英文版为准。 -->

# 编排协议

当主代理把规划、章节实现、完整章节评审、修复、自动硬上限再分解以及最终集成委托给相互独立的代理上下文时，使用本参考文档。

## 目录

1. [角色](#1-角色)
2. [上下文数据包](#2-上下文数据包)
3. [档位路由](#3-档位路由)
4. [章节编排算法](#4-章节编排算法)
5. [五轮硬上限恢复](#5-五轮硬上限恢复)
6. [提交与分支纪律](#6-提交与分支纪律)
7. [Worktree 与重试隔离](#7-worktree-与重试隔离)
8. [决策处理](#8-决策处理)
9. [状态完整性](#9-状态完整性)

## 1. 角色

### 主编排者

拥有功能契约、`PLAN-FULL.md`、依赖图、执行状态、子代理提示词、评审轮次记账、备份/重试分支选择以及最终接受门禁。它必须检查仓库状态，而不是信任代理的表述。

### 计划评审者

质疑初始章节边界、依赖、所有权、不变量、测试判定基准、兼容性、发布、回滚与集成检查点。它不负责实现。

### 章节实现者

接收一个已提取的章节与已冻结的契约。它只实现该章节，运行被要求的检查，并记录交接证据。

### 章节评审者

一个以 `SECTION` 模式运行 `code-review` 技能的全新 `[tier: review]` 上下文。每次计数评审都是对当前章节范围与直接语义影响锥的一次新的完整评审。在形成自己的观点之前，它不会收到先前的评审结论。

### 修复代理

一个接收当前轮次已冻结的代理可修复问题的 `[tier: review]` 上下文。它做最小的连贯修复，运行相关检查，并记录改动了什么。它不决定章节是否被接受。

### 硬上限分解者

一个干净的 `[tier: plan]` 子代理，仅在五轮完整评审未能产生一次干净的、覆盖完整的评审之后使用。它接收失败章节、原始章节基点、当前 `PLAN-FULL.md` 以及五份评审历史。它只把该章节拆分为更小的后代，并更新受影响的计划边；它不实现产品代码。

### 集成评审者

一个干净的评审者，在活跃叶子章节被接受之后，聚焦于跨章节组合与完整功能验收。

### 决策所有者

用户或负有责任的实际维护者。只有真正的产品语义、兼容性策略、迁移含义、可接受风险、发布行为或其他不可推断的业务选择需要该权限。

## 2. 上下文数据包

保持数据包显式。在独立性重要的场合，不要预载具有诱导性的历史。

### 实现者数据包

```text
Working path: {path}
Feature plan: .agent-work/PLAN-FULL.md
Current execution plan: .agent-work/PLAN.md
Section: {ID}
Section contract: .agent-work/sections/{ID}-CONTRACT.md
Section base: {section_base}
Feature invariants: {IDs}
Required checks: {commands}
Commit authority: {mode}
Do not implement future sections.
```

### 完整章节评审数据包

```text
Review mode: SECTION
Working path: {path}
Section: {ID}
Range: {section_base}..{section_head}
Feature contract: .agent-work/PLAN-FULL.md
Section contract: .agent-work/sections/{ID}-CONTRACT.md
Implementation handoff: .agent-work/sections/{ID}-HANDOFF.md
Output: .agent-work/reviews/{ID}-SECTION-r{NN}.md
Use: the code-review skill
```

不要包含先前的评审问题、上一轮是否干净的结论，或诸如“最终确认”之类的措辞。单次干净评审即接受这一规则由主编排者拥有，而不是由评审者拥有。

### 修复数据包

```text
Working path: {path}
Section: {ID}
Current reviewed head: {head}
Authorized findings from round {NN}: {IDs}
Review file: .agent-work/reviews/{ID}-SECTION-r{NN}.md
Frozen acceptance criteria: {criteria}
Section contract: .agent-work/sections/{ID}-CONTRACT.md
Required checks: {commands}
Do not broaden scope or fix unlisted speculative issues.
```

### 硬上限 `[tier: plan]` 数据包

```text
Task: Re-decompose one non-converging section. Do not implement product code.
Working path: {failed_working_path}
Feature plan: .agent-work/PLAN-FULL.md
Feature state: .agent-work/FEATURE-STATE.md
Current failed section: {ID} — {title}
Original section base: {section_base}
Failed tip: {failed_tip}
Backup branch: {backup_branch}
Hard-cap summary: .agent-work/replans/{ID}-g{generation}-HARD-CAP.md
Review files:
  - .agent-work/reviews/{ID}-SECTION-r01.md
  - .agent-work/reviews/{ID}-SECTION-r02.md
  - .agent-work/reviews/{ID}-SECTION-r03.md
  - .agent-work/reviews/{ID}-SECTION-r04.md
  - .agent-work/reviews/{ID}-SECTION-r05.md

The section failed to reach a clean, coverage-complete full SECTION review within five rounds.
Split only this section into smaller independently implementable, testable, and reviewable descendants.
Preserve accepted predecessor sections and user-owned feature semantics.
Use hierarchical lineage IDs such as {ID}.1, {ID}.2; recursively extend through depth 3 without pausing.
Treat the original section as depth 0. If the proposed descendants would be depth 4+, do not split yet: return a Human-decision packet for deeper-recursion approval or boundary re-planning.
Use the five review histories as decomposition evidence: repeated root causes must become explicit boundaries, invariants, oracles, or separate descendants.
Update requirement coverage, dependency edges, downstream Requires, checkpoints, and deferred-work ownership affected by the split.
Do not carry failed implementation choices forward merely because they already exist.
```

### 集成评审数据包

```text
Review mode: INTEGRATION
Working path: {path}
Feature range: {feature_base}..{feature_head}
Feature contract and requirement matrix: .agent-work/PLAN-FULL.md
Feature state: .agent-work/FEATURE-STATE.md
Section contracts/handoffs: .agent-work/sections/
Review/replan evidence: .agent-work/reviews/, .agent-work/replans/
Focus: full acceptance, cross-section contracts, migration, rollout/rollback,
security, reliability, operations, cleanup, and deferred-work closure.
Output: .agent-work/reviews/FEATURE-INTEGRATION-r01.md
Use: the code-review skill
```

## 3. 档位路由

把角色档位映射到宿主可用的子代理档位（见核心指令中的“模型路由档位”章节）：

- 常规章节实现：`[tier: execute]`；
- 高风险章节实现与修复：`[tier: review]`；
- 每次计数的完整 `SECTION` 评审：一个全新的 `[tier: review]` 评审者上下文；
- 五轮硬上限再分解：一个干净的 `[tier: plan]` 子代理；
- 最终集成评审：一个全新的 `[tier: review]` 评审者上下文，除非 governing instructions 另有规定。

`[tier: plan]` 分解者不是泛用的第六个评审者。它的任务是改变分解方式，而不是延续同一个搜索过程。

## 4. 章节编排算法

```text
for section in dependency_order(active_leaf_sections):
    section_base = accepted_predecessor_head(section)
    extract_to_PLAN(section)
    freeze_contract(section, section_base)

    run_implementer(section)
    inspect_repo_and_handoff()
    run_required_checks()
    commit_if_authorized("implementation")

    review_round = 0
    clean_streak = 0

    while review_round < 5:
        review_round += 1
        section_head = current_head()
        if review_round == 1:
            report = run_clean_full_SECTION_review(
                section_base,
                section_head,
                output=f"{section}-SECTION-r{review_round:02d}.md"
            )
        else:
            # After a repair, the acceptance review is scoped to the repair
            # delta plus its impact cone (see integration-and-convergence.md).
            report = run_post_repair_review(
                repair_base,
                section_head,
                cone=direct_semantic_impact_cone(),
                output=f"{section}-SECTION-r{review_round:02d}.md"
            )

        findings = main_agent_validate_and_deduplicate(report)

        if findings.require_user_decision():
            persist_state_and_block_for_decision()

        if findings.has_no_new_material_actionable_issue():
            # One coverage-complete clean review accepts the section.
            clean_streak += 1
            persist_round_state()
            accept_section_provisionally()
            break

        clean_streak = 0
        fixable = findings.agent_fixable_material_items()
        repair_base = section_head
        run_repair(fixable)
        inspect_repo_and_handoff()
        run_relevant_checks()
        commit_if_authorized("repair")
        persist_round_state()

    if not section_is_accepted():
        hard_cap_replan(section)
        replace_parent_with_active_descendants()
        continue_from_original_section_base()
```

### 什么算重大问题

一个新的 `Must Fix`（必须修复）、`Should Fix`（应当修复）或阻塞性 `Needs Decision`（需要决策）根因是重大问题。

以下情况通常不会重置连续干净记录：

- 已关闭根因的重复表述；
- 在当前中间状态有效的前提下，明确分配给后续章节的工作；
- 无依据的假设；
- 纯风格偏好；
- 非阻塞的 `Should Plan`（应当规划）或有界技术债。

主编排者依据评审报告与当前证据做这一记账决策。

### DELTA 检查

针对性的 DELTA 验证在一轮修复波次内部可能有用，尤其是对高风险修复。它不递增 `review_round`，也不能递增 `clean_streak`。只有全新的完整 `SECTION` 评审才计数。

## 5. 五轮硬上限恢复

没有软上限。唯一的评审轮次预算是每个活跃章节尝试五次完整 `SECTION` 评审。

若第 5 轮结束时章节未被接受（没有干净的、覆盖完整的完整评审）：

1. **不要运行第 6 轮。**
2. 确定下一个后代深度。若为 `1`–`3`，**不要询问是否继续**。若为 `4+`，保留证据并请求人类批准更深层递归或重新规划。
3. 持久化失败尝试与评审历史。
4. 在失败 tip 上创建 `agent-kit/backup/{feature-slug}-{section-id}-g{generation}-{timestamp}`。
5. 编写逐轮的硬上限摘要。
6. 对深度 `1`–`3`，使用上述数据包调用一个干净的 `[tier: plan]` 分解者。对深度 `4+`，除非人类授权更深层递归，否则在调用前停止。
7. 校验修订后的 `PLAN-FULL.md`。
8. 将失败父章节标记为 `SPLIT_AFTER_HARD_CAP` 并激活其后代。
9. 从失败父章节的原始 `section_base` 而非失败 tip 开始重试后代；直接连续执行到深度 `3`，不做进度暂停。

### 逐轮摘要

摘要必须保留证据，而不是含糊的“评审仍发现问题”式表述：

| Round | Reviewed head | New material findings | Root cause / boundary | Repair commit | Result |
|---|---|---|---|---|---|
| 1 | `<sha>` | `REV-...` | `<...>` | `<sha>` | findings |
| 2 | `<sha>` | `...` | `...` | `<sha>` | findings/clean |
| 3 | `<sha>` | `...` | `...` | `<sha>` | ... |
| 4 | `<sha>` | `...` | `...` | `<sha>` | ... |
| 5 | `<sha>` | `...` | `...` | `—` | hard cap |

还要说明反复出现的模式：契约耦合、所有权含糊、行为过多、判定基准薄弱、修复引发的相互作用，或其他有证据支撑的原因。

### 对 `[tier: plan]` 分解者的分解要求

一次有效的拆分必须做得比减少行数更多。后代应当分离以下一项或多项：

- 行为结果；
- 所有权/状态边界；
- 契约引入与消费方迁移；
- 在可独立交付/测试时，正常路径与高风险副作用路径；
- schema 展开与迁移与收缩；
- 策略求值与执行集成；
- 后台生产与消费/重试行为；
- 使能重构与可观察行为；
- 五次评审识别出的易出错的交互类别。

每个后代都需要一个独立的判定基准和一个稳定的中间仓库状态。

## 6. 提交与分支纪律

在 `EXECUTE_WITH_COMMITS` 模式下：

- 在首次评审之前提交初始的连贯章节实现；
- 在一次带有代理可修复重大问题的评审之后，在下一次完整评审之前做一个连贯的修复提交；
- 把无关的清理/用户工作排除在章节提交之外；
- 达到硬上限时，在创建备份引用之前，确保失败尝试中章节拥有的工作已提交；
- 备份分支在该技能被委托的权限下自动创建；
- 绝不自动推送/合并备份分支。

推荐的提交信息：

```text
feat(section-S03): implement <behavior>
fix(section-S03): address review round 2 findings
chore(agent): snapshot S03 before hard-cap replan
```

只有当章节拥有的被跟踪变更仍然存在时才需要快照提交。不要制造空的快照提交。

## 7. Worktree 与重试隔离

硬上限备份之后，优先从 `section_base` 新建重试分支/worktree，而不是重置失败分支。

推荐的重试分支：

```text
agent-kit/retry/{feature-slug}-{section-id}-g{next-generation}-{YYYYMMDD-HHMMSS}
```

规则：

- 失败的产品代码提交只保留在失败/备份谱系中；
- 默认不对它们做 cherry-pick；
- 延续修订后的规划/状态产物，而不是失败的产品代码差异；
- 若存在无关的脏的用户工作，保持其 worktree 不动，并创建隔离的重试 worktree；
- 在仓库根目录的 `.worktrees/` 工作区下创建重试 worktree，并按 manual-git-worktrees 技能的要求在 `.worktrees/current-agents/` 中登记重试任务；
- 用新的活跃路径/分支更新 `FEATURE-STATE.md`。

## 8. 决策处理

### 必须阻塞

- 必需的产品语义未定义；
- 两个权威来源冲突；
- 兼容性/迁移行为需要所有者选择；
- 可接受的风险或发布策略无法推断；
- `[tier: plan]` 的拆分需要改变已冻结的用户拥有需求。

### 不得仅为许可而阻塞

- 已达到第 5 轮评审；
- 需要创建备份分支；
- 需要调用 `[tier: plan]` 分解者；
- 需要拆分当前章节；
- 在已被委托的执行权限之下需要创建重试分支/worktree；
- 主代理需要提取第一个就绪的后代并继续。

## 9. 状态完整性

在每次交接之前，更新 `FEATURE-STATE.md`：

- 功能分支/worktree 与活跃重试路径；
- 章节 ID 与谱系；
- 章节 base/当前 head；
- 评审轮次与连续干净记录；
- 评审报告路径与重大问题 ID；
- 修复提交/检查结果；
- 重规划代数；
- 适用时的硬上限备份分支/失败 tip；
- 活跃后代与已退役父章节；
- 确切的下一步动作。

上下文压缩之后，先重读 `PLAN-FULL.md`、`FEATURE-STATE.md` 与当前 `PLAN.md`，再继续。

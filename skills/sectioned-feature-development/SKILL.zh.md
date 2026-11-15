---
name: sectioned-feature-development
description: "Plan and execute non-trivial software changes as reviewable sections with durable feature state, per-section contracts, independent implementation/review agents, single-clean-review section acceptance, delta-scoped post-repair re-review, a three-round hard cap escalated to a user decision, integration checkpoints, and a conditional final cross-section gate. Use when any trigger applies: the change crosses a high-risk semantic boundary; architecture or state ownership changes; the impact cone is difficult to bound; a previous whole-change implementation/review failed to converge; or expected behavioral edits exceed roughly 800 lines across more than three modules, packages, services, pages, or workflows."
---

<!-- 中文翻译版；英文原版为本目录同名 .md 文件。若两者不一致，以英文版为准。 -->

# 章节化功能开发（Sectioned Feature Development）

将一个大型功能开发为一系列有边界的章节（section）。每个章节必须可独立实现、可测试、可评审，且具有足以诊断的可回退性。第 1 轮评审是一次全新的、覆盖完整的完整 `SECTION` 评审；修复之后，下一个计数轮次是针对修复增量（repair delta）及其影响锥的 `DELTA` 评审，因此稳定范围绝不被重扫。当某个计数轮次未发现新的重大可执行问题时，该章节被暂时接受：一次干净的完整评审，或修复后一次 `delta-verified`（增量验证通过）的轮次。若三轮计数轮次仍未达到该条件，则保留失败尝试，并停在用户决策点上，给出有边界的选项——授权更多轮次、通过 `[tier: plan]` 再分解拆分章节、接受残余风险，或阻塞等待人工介入。

## 边界与权限

- 在使用本技能之前，先遵循仓库本地指令。
- 本技能用于单一功能、重构、迁移或架构演进，不用于周期性仓库审计。
- 在修改产品代码之前，先确定执行权限：
  - `PLAN_ONLY`：仅编写/校验规划产物。
  - `EXECUTE_NO_COMMIT`：实现并校验，但不执行分支/提交操作。
  - `EXECUTE_WITH_COMMITS`：创建/切换有边界的功能分支或重试分支/worktree，并进行章节实现/修复提交。
- 仅有规划或评审请求并不授权提交。
- 若 governing Custom Instructions 明确将分支/提交权限委托给 `sectioned-feature-development` 技能，则该限定范围的委托仅在本工作流的有边界功能/重试分支以及实现/修复/快照提交范围内，优先于其通用禁止提交规则。
- 绝不推送、合并、创建 pull request、改写已发布历史、清理、删除用户工作或丢弃无关变更，除非另行获得授权。
- 三轮评审硬上限**是**用户决策点。触发时，保留失败尝试，呈现有边界的选项，且只依据记录在案的用户选择行动；不得自主丢弃工作或开始重新实现。
- 从原始章节开始计数递归拆分深度：`S03` 为深度 `0`，`S03.1` 为深度 `1`，`S03.1.1` 为深度 `2`，`S03.1.1.1` 为深度 `3`。在硬上限决策中报告该深度；当拆分将产生深度 `4` 或更深时，建议对功能边界重新规划，而不是更深层递归。
- 当确实需要用户拥有的决策时仍须停止：产品语义、兼容性策略、迁移含义、可接受风险、发布行为，或其他不可推断的业务选择。

## 触发条件

当以下任一条件成立时使用本工作流：

- 变更跨越持久化、schema、资金、时间、单位、安全、权限、多租户、路由、并发、后台任务、公共 API、部署或共享状态边界。
- 架构或状态所有权发生变化。
- 影响锥难以界定。
- 此前对整个变更的实现或评审循环未能收敛。
- 预期行为性编辑大致超过 800 行**并且**跨越三个以上的模块、包、服务、页面或工作流。

仅规模本身（行数或模块数）绝不触发本工作流；语义风险与可评审性比原始行数更重要。常规规模的变更走正常的计划/实现/评审路径，单次评审即可。

## 必需产物

除非仓库规则定义了等价路径，否则使用以下路径：

```text
.agent-work/
├── PLAN-FULL.md
├── PLAN.md
├── FEATURE-STATE.md
├── sections/
│   ├── S01-CONTRACT.md
│   ├── S01-HANDOFF.md
│   └── ...
├── reviews/
│   ├── S01-SECTION-r01.md
│   ├── S01-SECTION-r02.md
│   └── ...
├── replans/
│   ├── S01-g01-HARD-CAP.md
│   └── ...
└── plans/
    └── {YYYYMMDD-HHMM}_FULL.md
```

保持 `PLAN-FULL.md` 与 `FEATURE-STATE.md` 的权威地位。聊天历史不是持久的项目状态。

## 渐进加载参考文档

- 在划分或重新划分功能之前，阅读 [references/section-planning.md](references/section-planning.md)。
- 在委托实现、评审、修复或硬上限恢复之前，阅读 [references/orchestration-protocol.md](references/orchestration-protocol.md)。
- 在接受章节或运行集成门禁之前，阅读 [references/integration-and-convergence.md](references/integration-and-convergence.md)。
- 在创建、提取、校验、延续或归档产物时，阅读 [references/artifact-schemas.md](references/artifact-schemas.md)。

## 状态机

```text
PREFLIGHT
  -> FEATURE_CONTRACT
  -> SECTION_PLAN
  -> PLAN_GATE
  -> SECTION_CONTRACT
  -> IMPLEMENT
  -> LOCAL_VALIDATE
  -> COMMIT_IF_AUTHORIZED
  -> REVIEW_ROUND (full on round 1 or after reset; DELTA after repair)
       -> CLEAN -> SECTION_ACCEPTED
       -> FINDINGS -> REPAIR -> COMMIT -> REVIEW_ROUND
       -> RESET_TRIGGER -> FULL_SECTION_REVIEW
       -> USER_DECISION -> BLOCK
       -> ROUND_3_WITHOUT_CLEAN -> HARD_CAP_DECISION
  -> SECTION_ACCEPTED
  -> INTEGRATION_CHECKPOINT when triggered
  -> next SECTION_CONTRACT
  -> CONDITIONAL_FINAL_INTEGRATION_REVIEW
  -> FINAL_VALIDATE
  -> ARCHIVE_AND_REPORT

HARD_CAP_DECISION (user)
  -> CONTINUE -> REVIEW_ROUND (up to two more counting rounds)
  -> SPLIT -> HARD_CAP_REPLAN (backup -> [tier: plan] split -> retry from original section base)
  -> ACCEPT_RISK -> SECTION_ACCEPTED_WITH_DEBT
  -> BLOCK
```

不要因为某个代理声称已完成就推进状态。只有当对应的产物与证据门禁得到满足时才推进。

## 阶段 0：预检与功能契约

1. 检查仓库规则、架构资料、当前分支、`git status`、相关的近期提交、构建/测试入口以及校验环境。
2. 冻结确切的 `feature_base` 提交。
3. 当 governing instructions 有要求时，优先使用仓库的代码图/索引。
4. 创建 `.agent-work/PLAN-FULL.md` 并记录：
   - 一句话目标；
   - 可观察行为；
   - 显式非目标；
   - 功能级不变量；
   - 权威约束；
   - 完整验收标准与校验命令；
   - 所有权/状态边界；
   - 兼容性、迁移、发布、回滚、开关、可观测性与清理要求。
5. 如果直接开发会显著恶化不安全的所有权边界或欠测试的核心路径，识别出最小的使能重构。
6. 在 `EXECUTE_WITH_COMMITS` 模式下，先创建功能分支，再实现产品代码。

## 阶段 1：划分功能

在实现之前，先在 `PLAN-FULL.md` 中创建所有初始章节。

优先采用：

1. 集成不确定时的行走骨架/契约验证；
2. 垂直行为切片；
3. 兼容性需要时，显式的展开-迁移-收缩或按抽象分支阶段；
4. 仅在消费方已迁移且证据证明旧路径无人使用之后进行清理/收缩。

每个章节都需要：

- 稳定 ID，例如 `S01`；
- 目标与可观察行为增量；
- 依赖/前驱关系；
- 预期涉及的文件/符号/工作流及语义边界；
- 非目标与指名的延后工作；
- 触及的功能不变量；
- 可证伪的验收标准；
- 确切的校验命令/证据；
- 兼容性/发布/恢复影响；
- 预估规模/风险与拆分触发条件。

一个合格的章节应当能让评审者在不加载整个功能实现的情况下理解，并且无需依赖未记录的未来工作即可验证。

在可行时使用辅助脚本：

```bash
python {skill-dir}/scripts/section_plan.py validate .agent-work/PLAN-FULL.md
python {skill-dir}/scripts/section_plan.py list .agent-work/PLAN-FULL.md
python {skill-dir}/scripts/section_plan.py extract \
  .agent-work/PLAN-FULL.md S01 --output .agent-work/PLAN.md
```

硬上限拆分之后，层级式后代 ID 有效，例如 `S03 -> S03.1, S03.2`，以及随后的 `S03.1 -> S03.1.1, S03.1.2`。

## 阶段 2：计划门禁

在实现之前，核实：

- 每一条完整功能需求都映射到章节证据与最终集成证据；
- 依赖显式且无环；
- 高风险边界各有一个权威所有者和一个判定基准（oracle）；
- 跨章节契约/检查点已被指名；
- 重构与行为已分离，除非不可分割；
- 没有章节是含糊的“完成/集成一切”式收纳桶；
- 每个章节都足够小，能在三轮评审预算下合理收敛。

对含糊/高风险计划使用一个干净的评审者。它质疑分解与契约；它不负责实现。

## 阶段 3：冻结一个当前章节

对下一个依赖就绪的章节：

1. 将 `section_base` 记录为确切的已接受前驱 head。
2. 将该章节原样提取到 `.agent-work/PLAN.md`。
3. 创建 `.agent-work/sections/{ID}-CONTRACT.md`。
4. 在写代码之前解决真正开放的业务决策。
5. 将原始章节的 `replan_generation` 设为 `0`，后代则继承/递增其谱系。
6. 更新 `FEATURE-STATE.md`：章节 ID、谱系、基点、执行路径、预期检查与评审轮次 `0`。

常规实现不得悄悄重定义已冻结的章节契约。

## 阶段 4：实现与本地校验

每次只委托一个当前章节。

按角色档位默认路由（映射到宿主可用的子代理档位；见核心指令中的“模型路由档位”章节）：

- 常规实现：`[tier: execute]` 子代理；
- 高风险实现或修复：`[tier: review]` 子代理；
- 章节评审：全新的 `[tier: review]` 子代理（评审者上下文）；
- 硬上限章节再分解：`[tier: plan]` 子代理。

实现者接收仓库规则、功能目标/不变量、当前 `PLAN.md`、章节契约、确切的 `section_base` 以及必需的检查。它不得实现未来章节。

要求：

- 满足章节契约的最小代码变更；
- 有意义的行为/边界/错误回归覆盖；
- 先做针对性检查，再做宽泛检查；
- `.agent-work/sections/{ID}-HANDOFF.md` 交接（handoff）文档，包含文件、决策、命令/结果、限制与 head。

在 `EXECUTE_WITH_COMMITS` 模式下，在评审之前提交完整的章节实现。

## 阶段 5：章节评审循环

第 1 轮评审是一次全新的、独立的、覆盖完整的 `SECTION` 模式 `code-review` 技能调用，范围为当前 `section_base..section_head` 加上直接语义影响锥。之后的每个计数轮次都是针对上一次修复增量及其失效影响锥的全新 `DELTA` 评审，因此稳定范围绝不被重扫。重置触发器生效时恢复完整 `SECTION` 评审。

每个计数轮次都使用一个干净的 `[tier: review]` 评审者子代理。不要预载先前评审者的推理、修复叙述，或之前轮次是否干净。要共享当前轮次冻结的问题 ID 以及累计的已关闭根因 ID 清单（仅 ID 与一行标题），使评审者不会重新提出已关闭的问题。

第 1 轮数据包：

```text
Review mode: SECTION
Section: {ID}
Range: {section_base}..{section_head}
Feature contract: .agent-work/PLAN-FULL.md
Section contract: .agent-work/sections/{ID}-CONTRACT.md
Implementation handoff: .agent-work/sections/{ID}-HANDOFF.md
Output: .agent-work/reviews/{ID}-SECTION-r{NN}.md
Use: the code-review skill
```

修复后数据包：

```text
Review mode: DELTA
Section: {ID}
Repair range: {repair_base}..{section_head}
Frozen findings from round {NN}: {IDs}
Closed root causes (IDs and one-line titles only): {list}
Feature contract: .agent-work/PLAN-FULL.md
Section contract: .agent-work/sections/{ID}-CONTRACT.md
Output: .agent-work/reviews/{ID}-SECTION-r{NN}.md
Use: the code-review skill
```

在 `FEATURE-STATE.md` 中维护 `review_round = 0`。

最多进行三轮计数轮次：

1. 递增 `review_round` 并运行该轮：第 1 轮或重置触发器生效后为完整 `SECTION` 评审，否则为 `DELTA` 评审。
2. 主代理检查报告与当前仓库状态。
3. 若某个问题需要真正的用户决策，记录它并立即阻塞。
4. 若**没有新的重大可执行问题**——覆盖完整的干净完整评审，或 `delta-verified` 的 DELTA 轮次——将该章节标记为 `section-accepted`。
5. 若出现任何新的 `Must Fix`（必须修复）、`Should Fix`（应当修复）或阻塞性 `Needs Decision`（需要决策）问题：
   - 将症状按稳定的根因 ID 去重；
   - 只把该轮中代理可修复的问题发给 `[tier: review]` 修复代理；
   - 运行相关的确定性检查；
   - 在 `EXECUTE_WITH_COMMITS` 模式下提交修复；
   - 更新交接文档与 `section_head`；
   - 将下一个计数轮次作为针对本次修复增量及其影响锥的 `DELTA` 评审运行；重置触发器生效时则运行完整 `SECTION` 评审。

以下情况不算重大问题，除非它们暗示冻结章节中存在重大缺陷：已关闭根因的重复表述、明确延后到未来章节的工作、无依据的假设、纯风格偏好、`Should Plan`（应当规划）或有界技术债。

修复波次内部仍可对高风险修复使用针对性检查；它们不推进 `review_round`——修复后的计数轮次本身就是 `DELTA` 评审。

### 三轮硬上限

在第 3 轮计数之后，若章节仍未被接受，**不要**开始第 4 轮。进入 `HARD_CAP_DECISION`：保留失败尝试（阶段 6.1），然后停下来请用户在以下记录在案的选项中选择：

- `continue`（继续）：为同一尝试授权最多两个额外计数轮次；
- `split`（拆分）：执行再分解协议（阶段 6.3 起）；
- `accept-risk`（接受风险）：接受当前实现，将剩余问题记录为显式债务/决策（`SECTION_ACCEPTED_WITH_DEBT`）；
- `block`（阻塞）：停下来等待针对根因的人工介入。

按上述顺序呈现选项，并附上逐轮证据。在谱系深度 `3` 时，建议对功能边界重新规划，而不是深度 `4+` 的拆分。将失败尝试的提交 cherry-pick 进重试，需要在同一决策中获得明确授权。

## 阶段 6：硬上限保留与用户决策

将三轮未收敛视为证据：当前章节边界对可靠的代理实现/评审而言可能过宽、耦合过重或隔离不足。保留失败尝试，然后停在硬上限用户决策点（阶段 5）。只有记录在案的 `split` 选择才进入下述再分解路径。

### 6.1 保留失败尝试

1. 记录 `failed_tip = HEAD`、`section_base`、当前章节 ID、重规划代数、全部计数轮次评审文件、修复提交与检查结果。
2. 在已授权提交的情况下，确保当前章节拥有的代码变更均已提交。绝不将无关的用户变更吸收进快照。
3. **无需请求授权**即创建备份分支：

```text
agent-kit/backup/{feature-slug}-{section-id}-g{generation}-{YYYYMMDD-HHMMSS}
```

让其指向 `failed_tip`。优先在不切换分支的情况下创建该引用。
4. 使用内置模板编写 `.agent-work/replans/{section-id}-g{generation}-HARD-CAP.md`。逐轮总结每个计数轮次各发现了什么、哪些根因已修复、什么问题反复出现，以及该章节为何未能收敛。记录用户决策、呈现的选项以及其授予的任何授权（额外轮次、salvage/cherry-pick、风险接受）。

备份是证据与恢复点。除非用户决策明确授权（`continue` 或 `accept-risk`），不要在那个失败的代码状态上继续实现。

### 6.2 呈现硬上限用户决策

停下来请用户按以下顺序选择：`continue`（最多两个额外计数轮次）、`split`（按阶段 6.3 再分解）、`accept-risk`（将剩余问题记录为显式债务/决策并标记 `SECTION_ACCEPTED_WITH_DEBT`）或 `block`（针对根因的人工介入）。附上逐轮证据与当前谱系深度；在深度 `3` 时，建议对功能边界重新规划，而不是深度 `4+` 的拆分。将选择记录到 `FEATURE-STATE.md` 与硬上限摘要中。

选择 `continue` 时，对同一尝试恢复阶段 5 计数轮次。选择 `accept-risk` 时，把每条剩余问题填入延后工作/残余风险台账。选择 `block` 时，停止。

### 6.3 将分解升级给 `[tier: plan]` 子代理（仅限拆分选择）

仅在用户记录 `split` 选择后进入。在启动 `[tier: plan]` 分解者之前，先计算该次拆分将产生的后代深度；深度为 `4+` 时，建议对受影响的父级/功能边界重新规划，而不是拆分。

启动一个干净的 `[tier: plan]` 子代理。明确告知它：

- 当前失败章节的 ID/标题及其 `section_base`；
- 功能目标、不变量与当前 `PLAN-FULL.md`；
- 备份分支与失败 tip；
- 全部计数轮次评审文件以及逐轮问题的简要总结；
- 已达到硬上限且用户选择了拆分；
- 它必须**只在 `PLAN-FULL.md` 中把当前章节拆分为更小的、可独立实现/评审的后代章节**；
- 已接受的前驱章节与用户拥有的功能语义已冻结；
- 它必须更新需求覆盖、依赖边、下游 `Requires`、检查点，以及受拆分影响的延后工作归属；
- 它不得实现产品代码；
- 后代应使用层级式谱系 ID，例如 `S03.1`、`S03.2`；若某个后代随后失败，继续该层级；
- 当前谱系深度；深度 `4+` 的后代需要记录在案的用户重新规划选择。

`[tier: plan]` 重规划必须把评审轮次历史用作分解证据：反复出现的 bug 类别应变成显式边界、不变量、判定基准或独立的后代章节，而不是以散文形式复制到一个看起来更小但语义相同的章节里。

### 6.4 主代理的计划改写与校验

`[tier: plan]` 子代理返回之后：

1. 主代理检查并在必要时规范化 `PLAN-FULL.md` 的拆分。`[tier: plan]` 子代理提出分解方案；主代理对最终产物的完整性负责。
2. 将父章节保留为历史谱系，状态为 `SPLIT_AFTER_HARD_CAP`；不再调度它。
3. 用 `section_plan.py` 校验修订后的 `PLAN-FULL.md`，核实依赖图仍无环且每条完整功能需求仍被覆盖。
4. 若提议的拆分需要新的用户拥有的产品决策，仅针对该决策阻塞。当后代深度将为 `4+` 时，在决策中建议对功能边界重新规划，而不是更深层拆分。
5. 更新 `FEATURE-STATE.md`：备份分支、失败 tip、硬上限摘要与用户决策、后代 ID 与下一个就绪后代。

### 6.5 从原始章节基点重试

**不要**把失败章节的实现或修复提交 cherry-pick 进重试，除非用户的硬上限决策明确授权保留（salvage）已验证部分。

从失败父章节的原始 `section_base` 开始后代序列：

- 在 `EXECUTE_WITH_COMMITS` 模式下，从 `section_base` 创建新的重试分支/worktree。优先新建分支/worktree，而不是重置失败分支。
- 只延续修订后计划/状态所需的编排产物；不延续失败的产品代码差异。
- 若无关的用户变更使切换分支不安全，保持失败 worktree 不动，并从 `section_base` 创建隔离的重试 worktree。
- 在仓库根目录的 `.worktrees/` 工作区下创建重试 worktree，并按 manual-git-worktrees 技能的要求在 `.worktrees/current-agents/` 中登记重试任务。
- 在 `FEATURE-STATE.md` 中记录新的重试路径/分支。

然后由**主代理**从修订后的 `PLAN-FULL.md` 中提取第一个依赖就绪的后代到 `.agent-work/PLAN.md`，并用常规的实现者/评审者代理恢复阶段 3 → 阶段 5。

硬上限拆分只通过用户重复的 `split` 决策递归进行。若某个后代（例如 `S03.1`）自身也达到三轮硬上限，保留该失败尝试并再次呈现决策；在谱系深度 `3` 时，建议对功能边界重新规划，而不是深度 `4+` 的拆分。

## 阶段 7：集成检查点

当公共契约、schema、权限模型、状态所有者、队列、部署路径、功能开关或依赖簇变得可被后续章节使用时，运行针对性检查点。

在不重开每一条已接受的局部代码的前提下，核验跨章节契约与代表性端到端路径。只有当实际的组合行为推翻了某章节已冻结的契约证据时，检查点才可以使该已接受章节失效。

只并行化满足以下条件的章节：依赖已被接受、语义所有者/契约相互独立、worktree 隔离、集成顺序确定。并行 worktree 必须遵循 `.worktrees/current-agents/` 登记册的冲突检查协议（见 manual-git-worktrees 技能）。

## 阶段 8：最终功能门禁

当所有活跃叶子章节均被接受且所有延后项均已解决或被明确批准后，收尾该功能。

仅当以下至少一条成立时，才对 `feature_base..feature_head` 运行最终的 `code-review` 技能 `INTEGRATION` 评审：

- 功能跨越了高风险语义边界；
- 被接受的活跃叶子章节超过三个；
- 发生过硬上限拆分；
- 用户或 governing instructions 明确要求。

否则跳过 `INTEGRATION` 评审：运行确定性的完整功能校验套件，并以该证据加上最后一个被接受章节的评审来判定就绪状态。不要在相同的组合范围上既运行晚期集成检查点又运行最终评审；最终评审涵盖检查点。

当评审运行时，关注章节评审单独无法证明的内容：

- 原始完整功能行为与非目标；
- 跨章节 API/schema/状态/权限/顺序/错误契约；
- 端到端关键路径与组合边界情况；
- 迁移、兼容性、发布、回滚、开关、清理；
- 可观测性、性能、安全、隐私、运维就绪、文档；
- 需求覆盖与分支范围完整性。

以有界范围修复集成问题，并重跑必要的集成证据。不要机械地重放所有已接受的章节评审。

然后运行确定性的完整功能校验套件，并将最终就绪状态判定为 `mergeable`（可合并）、`not-mergeable`（不可合并）或 `insufficient-evidence`（证据不足）。

## 阶段 9：归档与报告

1. 更新 `FEATURE-STATE.md`：每个活跃/退役章节的谱系、base/head、判定、评审轮次、备份分支、硬上限决策/重规划、检查、决策与残余风险。
2. 仅当其章节已被接受、拆分或明确放弃且持久产物已存在后，才删除临时的 `.agent-work/PLAN.md`。
3. 最终报告之后，将 `.agent-work/PLAN-FULL.md` 移动到 `.agent-work/plans/{YYYYMMDD-HHMM}_FULL.md`。
4. 保留契约、交接、评审证据与硬上限摘要，除非仓库策略另有规定。
5. 默认以中文报告：功能结果、章节谱系/状态、硬上限拆分、已修复的问题、检查、决策、集成结果、残余风险与可维护性判断。

## 不可协商的规则

- 一个实现者一次只处理一个已提取的章节/后代。
- 第 1 轮评审是来自干净评审者上下文的全新完整 `SECTION` 评审；除非重置触发器生效，之后的每个计数轮次都是针对修复增量及其影响锥的全新 `DELTA` 评审。
- 章节接受需要一个干净的计数轮次：覆盖完整的完整评审，或修复后 `delta-verified` 的轮次。
- 评审者独立性意味着不预载推理；共享冻结的问题 ID 与已关闭根因 ID（仅 ID 与标题）以防重新提出已关闭的问题。
- 三轮计数轮次是硬上限；超出它的任何轮次都需要明确记录在案的用户 `continue` 决策。
- 达到硬上限时，保留失败 tip 并呈现有边界的选项（continue / split / accept-risk / block）；绝不自主丢弃或重新实现。
- `split` 选择才会调用 `[tier: plan]` 子代理；深度 `4+` 的拆分应建议对功能边界重新规划。
- 拆分后的重新实现从失败父章节的原始基点开始，而不是从其被反复修复的代码开始，除非用户决策明确授权保留已验证部分。
- 失败尝试的提交保留在 `agent-kit/backup/***` 上，默认不进行 cherry-pick。
- 修复代理不得宣布自己的工作被接受。
- 新的用户拥有语义需要真正的决策；常规技术性分解不需要。
- 章节接受是暂时性的；条件性最终门禁（集成评审或完整校验套件）仍然适用。

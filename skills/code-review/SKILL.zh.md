---
name: code-review
description: "Review one bounded change set: a pull request, commit range, uncommitted diff, one implementation section, a repair delta, or a finished multi-section feature, especially AI- or agent-authored changes. Use for requested reviews, merge-readiness checks, and section acceptance. Runs one independent, evidence-backed full review, separates user-owned decisions from agent-fixable defects, and verifies repairs without rescanning stable scope."
---

# 代码评审

> 本文件是 `SKILL.md` 的中文译本,仅供阅读,不参与分发;如有出入以英文版为准。

以资深工程师的判断评审一个有界的变更集。目标是真实的合并风险和证据,而不是清单式走过场、反复全量扫描或风格意见。

## 边界

- 只评审指定的变更集。周期性的全仓库审计请使用 `code-audit` 技能。
- 默认只评审。只有用户或编排者明确授权时才修复。
- 代理编写的代码、摘要、PR 描述、测试声明和此前的评审结论,一律视为"看似合理但不可信"。
- 保护用户的工作。除非明确要求,不得 reset、clean、merge、批准、推送、发表评论或改写历史。
- 收到评审请求的子代理就是执行者,不得把同一次评审再次委派出去。

## 模式

- `FULL`:一个有界变更集——PR、提交范围、未提交的 diff,或一个分节范围 `base..head` 连同其计划/契约。整个功能的评审就是对 `feature_base..feature_head` 做 `FULL`;重点放在分节评审无法证明的内容上(跨节契约、端到端路径、迁移/发布顺序、需求覆盖、遗留脚手架),而不是逐行重放局部代码。
- `DELTA`:一次修复的 diff 加上它的直接影响锥,对照已冻结的发现项进行检查。绝不重新扫描稳定范围。

对于分节范围,还要验证:已冻结的验收标准、该节触及的功能级不变量、在后续分节完成之前仓库/运行时的中间状态是否有效,以及延期工作是否明确且可以安全推迟。已明确延期到后续分节的工作不要报为缺陷。分节验收是临时性的,绝不代表整个功能可合并。

## 深度

选择一个深度;模式与深度相互独立。

- `Small`:狭窄的局部行为,文件少,不涉及信任、数据、并发、迁移、发布或公共契约边界。
- `Medium`:多个模块或工作流、共享辅助函数、有实质意义的 UI 行为、与 API 或持久化相邻的逻辑。
- `Large`:重构、状态模型重写、迁移、认证/权限变更、并发或后台任务、破坏性操作、架构转换、大范围配置/CI 变更,或影响锥难以界定。

任何高风险语义边界——安全、权限、持久化/schema、金额、时间、并发、公共 API——无论 diff 多小,都强制为 `Large`。

`Large` 深度、AI 编写的变更,或涉及代理工具、提示词、权限、CI 的变更,请阅读 [references/checklist.md](references/checklist.md)。

先指出可评审性差的问题(混杂无关目标、意图不清、巨量生成代码、基线不稳定、缺少构建环境),然后基于现有的最高价值证据继续评审,不要凭空制造确定性。

## 流程

1. **确立现实。** 记录模式、精确的 base 与 head(或可复现的 diff 命令)以及 `git status`。阅读与变更相关的仓库规则、计划/契约和测试入口。记下哪些检查在当前环境确实能跑。
2. **重建意图。** 依据仓库中的权威证据,写出一句话意图、明确的非目标,以及必须保持成立的不变量。"向后兼容"、"仅测试改动"、"所有测试通过"之类的说法是待验证的声明,不是降低审查力度的理由。
3. **绘制变更与影响锥。** 变更的入口点、公共 API、schema、权限、状态所有者、任务、配置和 CI;直接调用方与被调用方;被移除的行为;新引入的假设。
4. **生成候选问题,不改代码。** 做一次广泛的发现扫描,按以下视角顺序:产品/领域语义与端到端正确性;数据、状态、顺序、并发、失败原子性;安全、隐私、权限、信任边界;可靠性、发布、回滚、可观测性、性能;架构、复用、不必要的复杂度;测试与 CI 完整性;适用时的 AI 代理风险。`Medium` 和 `Large` 至少端到端追踪一条关键路径。仅凭 diff 无法证明行为时,阅读未变更的上下文。接受新抽象之前先搜索已有实现。
5. **验证与证伪。** 对每个候选:写明确切的触发条件和被违反的不变量,追踪可达路径,然后尝试用代码、类型、测试、配置或最小可运行检查去推翻它。丢弃缺乏支持的候选。绝不发布未经验证的假设。
6. **去重。** 把多个症状合并为一个根因发现项,赋予稳定 ID(`REV-001`),并附上所有受影响的实例。

## 发现项

每个发现项都要写明:严重级别、文件/符号引用、触发条件、影响、已检查的证据(及剩余的不确定性),以及最小可信的修复方向。

| 严重级别 | 含义 |
|---|---|
| `Must Fix` | 阻塞合并:正确性、安全、隐私、数据丢失、权限、迁移或发布风险。 |
| `Should Fix` | 合并前应修复,除非用户明确接受该风险。 |
| `Needs Decision` | 由用户决定:产品语义、兼容性策略、迁移含义、可接受风险。绝不猜测,要问。 |
| `Note` | 不阻塞:计划中的后续工作、有界的技术债,或值得记录的证据缺口。 |

不要报告:格式或仅 linter 能发现的问题、同等有效写法之间的偏好、没有可达触发条件的假想问题、未指明缺失行为的"多加测试"、没有合理规模依据的性能担忧,或缺少资产、路径和影响的安全标签。测试通过不能证明产品语义、安全或迁移安全是正确的。

## 修复与验证

每个变更集只做一次独立的完整评审。不存在多轮评审循环。

1. **冻结** 发现项的 ID、措辞、证据和验收标准,然后才能修复。修复者不得在修复过程中重新定义发现项。
2. **先停下来**:当某个 `Needs Decision` 项导致无法安全修复时,只询问继续所必需的决策。
3. **修复**(仅在获得授权时):针对已冻结的、代理可修复的发现项,做最小且内聚的改动。不做无关清理。
4. **自验**(主代理/编排代理):运行相关检查,并对照每个已冻结的发现项重新阅读修复 diff。只有在代码中可见的证据加上检查通过时才关闭发现项——绝不仅凭修复者的解释关闭。
5. **独立 `DELTA` 评审** 仅在修复本身触及高风险语义边界(见"深度"一节)或用户要求时进行。使用全新的评审者。
6. **仍未解决?** 若第 4 步(或已执行的第 5 步)之后仍有 `Must Fix` 或 `Should Fix` 未关闭,停下来把决定权交给用户:授权继续修复、拆分变更、接受风险,或阻塞。不要自行开启新一轮。

`DELTA` 评审者只检查:修复改动的代码块;被修复影响而失效的调用方、契约、schema、权限和测试;以及每个已冻结的发现项是否确实关闭。当修复重写了原变更的相当一部分、扩大了范围,或 base/head 在修复之外发生了移动时,它返回 `reset-required` 而不是结论——由用户决定是否重新做一次 `FULL` 评审。

## 评审者独立性

- 在全新的 `[tier: review]` 上下文中执行评审,与作者和修复者分开。
- 只给 `FULL` 评审者提供范围、计划/契约和本技能。不要泄露怀疑的问题、此前的结论或修复叙述。
- 给 `DELTA` 评审者提供修复范围、已冻结的发现项 ID,以及已关闭根因的一行标题——不提供此前推理中的任何其他内容。

## 结论

- `FULL`:`mergeable` | `not-mergeable` | `insufficient-evidence`。分节范围则为:`accepted` | `blocked` | `insufficient-evidence`。
- `DELTA`:`delta-verified` | `delta-blocked` | `reset-required`。

给出肯定结论必须同时满足:没有未关闭的 `Must Fix`;没有用户尚未接受的 `Should Fix`;没有阻塞性的 `Needs Decision`;必需的确定性检查通过,或已说明其阻碍因素和残余风险。一次干净的评审就足够——绝不要求第二次空结果的评审。

## 报告

面向用户的报告默认用中文撰写。代码符号、路径、命令、错误文本和发现项 ID 保持原样。先按严重级别列出发现项;若没有可操作的发现项,直接说明并陈述残余风险。区分已验证的事实、推断和未验证的声明。除非当前代码和验证证据支持,否则绝不声称某个发现项已解决。

只有在编排者要求,或评审必须跨越上下文压缩时,才写报告文件:`.agent-work/reviews/{id}-r{N}.md`(`{id}` 为分节 ID 或简短的变更标识)。不保留其他账本。模板:

```markdown
# Review {id} r{N}

- Mode / depth: FULL | DELTA / Small | Medium | Large
- Range: {base}..{head} (or diff command); worktree state
- Verdict: ...
- Intent and invariants: ...

## Findings

### REV-001 — {root-cause title}
- Severity: Must Fix | Should Fix | Needs Decision | Note
- Where: {file:line, symbol, route}
- Trigger: ...
- Impact: ...
- Evidence: ... (uncertainty: ...)
- Fix direction: ...
- Status: open | fixed-verified | accepted-risk | deferred

## Coverage

- Lenses and critical paths reviewed: ...
- Checks run / not run (with reason): ...
- Residual risk and assumptions: ...
```

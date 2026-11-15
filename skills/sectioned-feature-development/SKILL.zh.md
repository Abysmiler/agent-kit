---
name: sectioned-feature-development
description: "Plan and execute one large, high-risk change as 2-6 reviewable sections with a single plan file, a single state file, one independent review per section, and main-agent verification after repair. Use only when (A) the change crosses a high-risk semantic boundary (persistence/schema, security/permissions, money, time, concurrency/background jobs, public API, shared state ownership) AND is large (roughly 800+ lines of behavioral edits across more than 3 modules); or (B) a previous whole-change implementation or review failed to converge; or (C) the user asks for sectioned development. Size alone or risk alone does not trigger it."
---

> 中文译本,仅供阅读,不参与分发;与 `SKILL.md` 不一致时以英文版为准。

# 分节功能开发

把一个大功能拆成一小串有边界的节来交付。每一节依次完成:实现、验证、由独立评审者评审一次、必要时修复、由主代理核验,然后才开始下一节。

## 触发条件

仅当满足以下之一时使用本流程:

- **A.** 改动跨越高风险语义边界(持久化/表结构、安全/权限、金额、时间、并发/后台任务、公共 API、共享状态归属),**并且**规模大:行为性改动约 800 行以上且涉及 3 个以上模块。
- **B.** 此前对这项工作的整体实现或评审未能收敛。
- **C.** 用户明确要求。

仅规模大或仅风险高都不触发。这类改动走普通路径:实现、验证,可选做一次 `code-review`。

## 权限

仓库本地规则优先。动产品代码之前先确定一种模式:

- `PLAN_ONLY`:只写 `.agent-work/PLAN.md`。
- `EXECUTE_NO_COMMIT`:实现并验证;不做分支或提交操作。
- `EXECUTE_WITH_COMMITS`:核心规则中的限定例外授权创建一个功能分支,并为每节的实现和每次修复各做一次提交。

仅有计划或评审请求不构成提交授权。绝不 push、merge、创建 pull request、改写历史、reset、clean 或删除用户的工作。绝不把无关的未提交用户改动带进某一节的提交。

遇到真正属于用户的决策时停下:产品语义、兼容性策略、迁移含义、可接受的风险。普通的技术拆分不需要停下来征求许可。

## 产物

```text
.agent-work/
├── PLAN.md                        # 功能契约 + 全部节
├── STATE.md                       # 实时状态;每一步之后更新
├── reviews/{section-id}-r{N}.md   # 由 code-review 技能写入
└── plans/{YYYYMMDD-HHMM}.md       # 完成后归档的 PLAN.md
```

状态保存在这些文件里,而不是对话里。上下文压缩之后或恢复工作时,先重读 `PLAN.md` 和 `STATE.md`,再做其他事。

`PLAN.md` 模板:

```markdown
# {功能标题}

- Outcome: {一句话结果}
- Non-goals: {明确不做的范围}
- Invariants: {在每个中间状态和最终状态都必须成立的事实}
- Acceptance: {可观察、可证伪的标准}
- Validation: {完整验证套件的确切命令}

## S01 — {标题}
- Goal: {一个可观察的行为增量}
- Depends on: {节 ID 或 none}
- Scope: {预计涉及的文件/模块/流程;延后了什么,延后到哪一节}
- Acceptance: {可证伪的标准}
- Validation: {确切命令}
```

`STATE.md` 模板:

```markdown
# State — {功能标题}

- Mode: {PLAN_ONLY | EXECUTE_NO_COMMIT | EXECUTE_WITH_COMMITS}
- Branch: {分支名}    Feature base: {sha}
- Next step: {下一步具体要做什么}

| Section | Status | Base | Head | Review verdict |
|---|---|---|---|---|
| S01 | pending / in-progress / in-review / accepted / accepted-with-debt / split / blocked | {sha} | {sha} | {clean / findings repaired / ...} |

## Open decisions
## Accepted debt
```

## 1. 计划

1. 检查仓库规则、分支、`git status` 以及构建/测试入口。记录 `feature_base` 提交。
2. 写出功能契约,然后把工作拆成 **2-6 节**:
   - 默认采用纵向切片:一个连贯的行为,只穿过让它真实可用、可测试所必需的层。
   - 集成路径不确定时,先做一条薄的端到端骨架。
   - 使能性重构与行为变更分开,且重构必须保持行为不变。
   - 不兼容的表结构或 API 变更按"扩展、迁移、收缩"排序;旧路径最后移除。
   - 不要按层、目录或文件类型拆分。
3. 计划关卡(自查,不另起评审者):
   - 每条验收标准都对应到某一节;
   - 依赖关系明确且无环;
   - 每一节都能独立测试和评审,不依赖未记录的后续工作;
   - 没有"收尾/把一切集成起来"式的兜底节。
4. 向用户展示计划。在写代码前解决属于用户的未决决策。`PLAN_ONLY` 模式到此为止。
5. `EXECUTE_WITH_COMMITS` 模式下创建功能分支。创建 `STATE.md`。

## 2. 节循环

每次只处理一个依赖已就绪的节。

1. **冻结。** 在 `STATE.md` 中记录 `section_base`(当前 head);把该节标为 `in-progress`。实现过程不得悄悄改变该节的范围或验收标准。
2. **实现**且只实现这一节:使用 `[tier: execute]` 子代理;该节本身高风险时使用 `[tier: review]`。交给它仓库规则、`PLAN.md`、节 ID 和 `section_base`。要求用满足验收标准的最小改动,并附带有意义的行为、边界和错误测试。
3. **验证。** 运行该节的验证命令。检查失败时不得继续。
4. 获得授权时**提交**该节。记录 `section_head`。
5. **评审一次。** 在全新的 `[tier: review]` 上下文中调用 `code-review` 技能:

   ```text
   Review mode: FULL
   Range: {section_base}..{section_head}
   Contract: .agent-work/PLAN.md, section {ID}
   Output: .agent-work/reviews/{ID}-r1.md
   ```

   不要预先灌入实现者的推理或结论。
6. 评审**无问题**:把该节标为 `accepted`,继续下一节。
7. **有发现:** 冻结发现清单,然后只修复代理可修的项(`[tier: review]`),重跑验证,并提交修复。修复代理不得自行宣布其工作已通过。
8. **主代理核验。** 重跑检查,并对照每条已冻结的发现重读修复差异:它是否已关闭,修复是否引入了新问题?只有当修复本身触及高风险边界时,才对修复范围做一次独立的 `DELTA` 模式 `code-review`(输出 `{ID}-r2.md`)。
9. 核验无问题:标为 `accepted`。**仍有问题:停下**,请用户选择:
   - `continue`:再做一次修复加核验;
   - `split`:把这一节重新规划为更小的节;
   - `accept-risk`:把剩余发现记入 Accepted debt,并标为 `accepted-with-debt`;
   - `block`:停下等待人工介入。

   给出选项时附上未解决的发现和证据。未经用户选择,绝不丢弃工作或开始重新实现。
10. 选择 `split` 时:给失败的 head 打标签 `agent-kit/failed/{section-id}`,把该节标为 `split`,以评审发现作为拆分依据,在 `PLAN.md` 中把它改写为更小的节(`S03a`、`S03b`),重跑计划关卡,并从 `section_base` 重新开始。只有用户授权时才复用失败尝试中的代码。

每一步之后更新 `STATE.md`,包括 `Next step`。

只有通过 `manual-git-worktrees` 技能才能并行执行相互独立的节。

## 3. 最终关卡

1. 运行 `PLAN.md` 中的完整验证命令。
2. 只有发生过 `split` 或 `accept-risk`,或用户要求时,才对 `feature_base..feature_head` 做一次最终的 `FULL` 模式 `code-review`,聚焦跨节组合(节与节之间的契约、端到端路径、迁移与回滚)。在有界范围内修复发现,并按节循环的方式核验。
3. 把 `PLAN.md` 移到 `.agent-work/plans/{YYYYMMDD-HHMM}.md`。保留 `STATE.md` 和 `reviews/` 作为证据。
4. 默认用中文报告:
   - 就绪状态:`mergeable`、`not-mergeable` 或 `insufficient-evidence`;
   - 各节状态表、已修复的发现、运行过的检查及结果;
   - 做出的决策、已接受的债务、残余风险;
   - 简短的维护性判断。

## 规则

- 一次一节;绝不提前实现后面的节。
- 依据证据(检查通过、评审文件)推进,而不是依据代理声称已完成。
- 每节一次独立评审。修复之后由主代理核验;`DELTA` 评审是例外,不是默认。
- 修复并核验后仍有问题,意味着交给用户决策,绝不自行追加一轮。
- 在最终关卡通过之前,节的验收都是暂定的。

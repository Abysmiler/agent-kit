<!-- 中文翻译版；英文原版为本目录同名 .md 文件。若两者不一致，以英文版为准。 -->

# 硬上限重规划：<章节 ID — 标题>

## 失败尝试

- Feature: `<name>`
- Parent section: `<Sxx / Sxx.n>`
- Parent lineage: `<...>`
- Replan generation: `<n>`
- Original section base: `<commit>`
- Failed tip: `<commit>`
- Backup branch: `agent-kit/backup/<...>`
- Failed working path: `<path>`
- Hard cap: `5 full SECTION reviews`
- Required acceptance: `a clean, coverage-complete full SECTION review`

## 五轮评审

| 轮次 | 被评审 head | 新的重大问题 | 根因 / 边界 | 修复提交 | 结果 |
|---:|---|---|---|---|---|
| 1 | `<sha>` | `<REV ids / none>` | `<...>` | `<sha / —>` | `findings / clean` |
| 2 | `<sha>` | `<...>` | `<...>` | `<...>` | `<...>` |
| 3 | `<sha>` | `<...>` | `<...>` | `<...>` | `<...>` |
| 4 | `<sha>` | `<...>` | `<...>` | `<...>` | `<...>` |
| 5 | `<sha>` | `<...>` | `<...>` | `<...>` | `hard-cap / clean` |

## 评审工件

- `.agent-work/reviews/<ID>-SECTION-r01.md`
- `.agent-work/reviews/<ID>-SECTION-r02.md`
- `.agent-work/reviews/<ID>-SECTION-r03.md`
- `.agent-work/reviews/<ID>-SECTION-r04.md`
- `.agent-work/reviews/<ID>-SECTION-r05.md`

## 收敛诊断

- 反复出现的根因类别：<...>
- 耦合的所有权/契约：<...>
- 薄弱或过宽的判定基准：<...>
- 修复引发的相互作用：<...>
- 支撑本次拆分的证据：<...>

## [tier: plan] 再分解请求

- 只拆分该父章节。
- 保留已接受的前驱章节与用户拥有的功能语义。
- 使用层级式后代 ID。
- 更新需求覆盖、依赖边、下游 `Requires`、检查点，以及延后工作归属。
- 不实现产品代码。
- 不得在没有依据评审证据重新推导边界的情况下，照搬失败的实现结构。

## 产生的后代

| ID | 目标 | 依赖 | 独立判定基准 | 评审风险降低 |
|---|---|---|---|---|
| `<Sxx.1>` | <...> | <...> | <...> | <...> |
| `<Sxx.2>` | <...> | <...> | <...> | <...> |

## 重试

- 父章节状态：`SPLIT_AFTER_HARD_CAP`
- 重试起点：`<original section base>`
- 重试分支/worktree：`<agent-kit/retry/...>`
- 第一个就绪后代：`<Sxx.1>`
- 是否 cherry-pick 失败实现的提交：`no`

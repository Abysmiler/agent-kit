<!-- 中文翻译版；英文原版为本目录同名 .md 文件。若两者不一致，以英文版为准。 -->

# 功能状态：<Feature Name>

## 1. 当前状态

- Mode: `PLAN_ONLY | EXECUTE_NO_COMMIT | EXECUTE_WITH_COMMITS`
- Working path: `<path>`
- Active feature/retry branch: `<branch/path or N/A>`
- Feature base: `<commit>`
- Current head: `<commit or diff fingerprint>`
- Current state: `<state>`
- Active section: `<Sxx / Sxx.n or none>`
- Parent lineage: `<none or Sxx -> Sxx.n>`
- Replan generation: `<0+>`
- Review round: `<0..3；超过 3 仅凭记录在案的用户 continue 决策>`
- Next action: `<exact next gate>`
- Last updated: `<timestamp>`

## 2. 功能契约摘要

- 目标：<...>
- 非目标：<...>
- 全局不变量：`INV-01`, `INV-02`
- 计划：`.agent-work/PLAN-FULL.md`

## 3. 章节状态与谱系

| ID | 父章节 | 状态 | Base | Head | 评审轮次 | 重规划代数 | 契约 | 评审/交接 |
|---|---|---|---|---|---:|---:|---|---|
| S01 | — | PLANNED | — | — | 0 | 0 | — | — |

有效状态包括 `PLANNED`、`CONTRACT_FROZEN`、`IMPLEMENTED`、`UNDER_REVIEW`、`REPAIRING`、`SECTION_ACCEPTED`、`SECTION_ACCEPTED_WITH_DEBT`、`SPLIT_AFTER_HARD_CAP`、`BLOCKED`。

## 4. 需求覆盖

| 需求 | 活跃章节证据 | 集成证据 | 状态 |
|---|---|---|---|
| R-01 | — | — | planned |

## 5. 未决问题

| 问题 | 严重度/类别 | 章节/轮次 | 是否冻结验收 | 评审文件 | 状态 |
|---|---|---|---|---|---|
| — | — | — | — | — | none |

## 6. 决策

| ID | 决策 | 权限/来源 | 受影响范围 | 状态 |
|---|---|---|---|---|
| D-01 | <...> | <...> | Sxx | accepted/open |

## 7. 检查与证据

| 时间 | 范围 | 命令/证据 | 结果 | 工件 |
|---|---|---|---|---|
| <...> | S01 | `<command>` | pass/fail/blocked | `<path>` |

## 8. 硬上限重规划

| 父章节 | 代数 | 原始基点 | 失败 tip | 备份分支 | 用户决策 | 摘要 | 后代 | 重试分支/worktree |
|---|---:|---|---|---|---|---|---|---|
| — | — | — | — | — | — | — | — |

## 9. 集成检查点

| ID | 包含的活跃章节/head | 契约/路径 | 结果 | 证据 |
|---|---|---|---|---|
| CP1 | — | — | planned | — |

## 10. 重置 / 证据失效事件

| ID | 时间 | 触发原因 | 旧基线 | 新基线 | 失效证据 |
|---|---|---|---|---|---|
| — | — | — | — | — | none |

## 11. 延后工作与残余风险

| ID | 事项/风险 | 合并前是否必需？ | 所有者 | 状态/接受方式 |
|---|---|---|---|---|
| — | — | — | — | none |

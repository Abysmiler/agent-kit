<!-- 中文翻译版；英文原版为本目录同名 .md 文件。若两者不一致，以英文版为准。 -->

# 完整实施计划：<Feature Name>

- 创建时间：<YYYY-MM-DD HH:MM TZ>
- 工作模式：`PLAN_ONLY | EXECUTE_NO_COMMIT | EXECUTE_WITH_COMMITS`
- 仓库：`<path>`
- Feature 分支/worktree：`<branch or N/A>`
- Feature base：`<commit>`
- 计划版本：`v1`
- 当前状态：`PLANNING`

<!-- FEATURE-CONTEXT:START -->
## 功能契约

### 一句话目标

<明确说明完成后系统新增或改变的结果。>

### 用户/操作者可观察行为

- <行为 1>
- <行为 2>

### 非目标

- <明确不做什么>

### 全局不变量

- `INV-01`：<每个章节（section）和最终结果都必须保持的事实>
- `INV-02`：<安全、数据、状态或兼容性不变量>

### 硬约束与权威来源

| ID | 约束 | 权威来源 |
|---|---|---|
| C-01 | <约束> | `<repo path / issue / decision>` |

### 完整功能验收标准

- `R-01`：<行为级标准>
- `R-02`：<行为级标准>

### 完整功能验证命令

```bash
<command>
```

### Ownership / State Boundary

| 边界 | 权威所有者 | 消费方 | 风险 |
|---|---|---|---|
| <state or decision> | `<module>` | `<modules>` | `<risk>` |

### Compatibility / Migration / Rollout / Rollback

- 兼容策略：<...>
- 迁移策略：<...>
- 发布/开关：<...>
- 回滚/恢复：<...>
- 可观测性：<...>
- 临时机制清理条件：<...>
<!-- FEATURE-CONTEXT:END -->

## 需求覆盖矩阵

| 需求 | 主要章节 | 章节判定基准 | 集成判定基准 | 状态 |
|---|---|---|---|---|
| R-01 | S01 | <test/check> | CP1 / FINAL | planned |
| R-02 | S02 | <test/check> | FINAL | planned |

## 章节索引与依赖图

| ID | 父章节 | 重规划代数 | 标题 | 类型 | 依赖 | 集成于 | 风险 | 状态 |
|---|---|---:|---|---|---|---|---|---|
| S01 | — | 0 | <title> | vertical | — | CP1 | medium | planned |
| S02 | — | 0 | <title> | enabling/expand/migrate/contract | S01 | CP1 | high | planned |

```text
S01 -> S02 -> CP1 -> FINAL
```

## 集成检查点

### CP1 — <名称>

- 包含章节：`S01`, `S02`
- 被证明的契约：<...>
- 关键路径：<...>
- 命令/证据：<...>
- 回滚/停用路径：<...>

## 计划门禁

- [ ] 每条需求都映射到章节证据与集成证据。
- [ ] 依赖图无环。
- [ ] 每个高风险边界都有所有者与判定基准。
- [ ] 每个章节都可独立实现、测试与评审。
- [ ] 跨章节契约与检查点已显式化。
- [ ] 重构与行为已分离，或已论证不可分离。
- [ ] 并行章节不共享同一语义所有者。
- [ ] 发布、回滚、迁移、可观测性与清理均已覆盖。
- [ ] 不残留最终的“集成一切”式收尾章节。

## 章节列表

<!-- SECTION:S01:START -->
## S01 — <章节标题>

### 目标

<本章节唯一主要目标。>

### 行为增量

- <完成后可观察、可验证的行为>

### 依赖

- Requires: `none`
- Integrates with: `CPx | none`
- Expected predecessor head: `<filled when contract freezes>`

### 预计范围

- Lineage: `original`
- Replan generation: `0`
- Files/symbols/workflows: `<expected scope>`
- Semantic boundaries: `<persistence/security/API/etc.>`
- Estimated behavioral size: `<range>`
- Risk: `low | medium | high`
- Split trigger: <when to stop and split again>

### 非目标

- <本章节明确不处理的内容>

### 全局不变量

- `INV-01`
- <section-specific invariant>

### 验收标准

- `S01-AC-01`：<具体、可证伪的标准>
- `S01-AC-02`：<边界/失败标准>

### 验证命令

```bash
<targeted test/lint/typecheck/runtime command>
```

保留证据：<log, screenshot, response, migration result, etc.>

### 发布与恢复

- Intermediate state validity: <...>
- Compatibility/migration: <...>
- Flag/rollout: <...>
- Rollback/recovery: <...>
- Observability: <...>

### 延后项

- <none or assign to a named existing section>
<!-- SECTION:S01:END -->

<!-- SECTION:S02:START -->
## S02 — <章节标题>

### 目标

<...>

### 行为增量

- <...>

### 依赖

- Requires: `S01`
- Integrates with: `CP1`
- Expected predecessor head: `<filled when contract freezes>`

### 预计范围

- Lineage: `original`
- Replan generation: `0`
- Files/symbols/workflows: `<...>`
- Semantic boundaries: `<...>`
- Estimated behavioral size: `<...>`
- Risk: `high`
- Split trigger: <...>

### 非目标

- <...>

### 全局不变量

- `INV-01`

### 验收标准

- `S02-AC-01`：<...>

### 验证命令

```bash
<command>
```

### 发布与恢复

- Intermediate state validity: <...>
- Compatibility/migration: <...>
- Flag/rollout: <...>
- Rollback/recovery: <...>
- Observability: <...>

### 延后项

- <none or assigned section>
<!-- SECTION:S02:END -->

## 决策台账

| ID | 问题 | 决策/权限 | 受影响章节 | 状态 |
|---|---|---|---|---|
| D-01 | <question> | <decision or pending> | S02 | open |

## 延后工作台账

| ID | 事项 | 功能契约是否要求？ | 所有者章节/后续跟进 | 状态 |
|---|---|---|---|---|
| DW-01 | <item> | yes/no | S02 / follow-up issue | planned |

## 重规划历史

| 版本 | 日期 | 触发原因 | 失效的章节/证据 | 决策 |
|---|---|---|---|---|
| v1 | <date> | initial | — | — |

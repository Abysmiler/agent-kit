<!-- 中文翻译版；英文原版为本目录同名 .md 文件。若两者不一致，以英文版为准。 -->

# 章节契约：<Sxx — 标题>

## 标识与基线

- Feature: `<name>`
- Section: `<Sxx / Sxx.n>`
- Parent section: `<none or Sxx>`
- Lineage: `<Sxx -> Sxx.n or original>`
- Replan generation: `<0+>`
- Contract revision: `1`
- Frozen at: `<timestamp>`
- Section base: `<commit or fingerprint>`
- Dependency heads: `<Syy=commit>`
- Plan fingerprint: `<sha256>`
- Implementer tier: `<tier: execute or tier: review>`
- Reviewer tier: `tier: review` （全新评审者上下文）
- Acceptance rule: `a clean, coverage-complete full SECTION review within 5 rounds`

## 目标

<一个连贯的结果，或一个使能接缝>

## 可观察行为增量

- <行为>

## 范围与语义边界

- 预期的文件/符号/工作流：<...>
- 被修改的所有者：<...>
- 高风险边界：<...>
- 明确允许的机械性/生成性变更：<...>

## 非目标

- <...>

## 功能级不变量

- `INV-01`：<...>
- `INV-02`：<...>

## 章节验收标准

- `Sxx-AC-01`：<触发条件、预期行为、证据>
- `Sxx-AC-02`：<负面或失败行为>

## 验证

```bash
<command>
```

- 运行时/手工证据：<...>
- 可能无法执行的检查及其阻塞处理策略：<...>

## 兼容性、迁移、发布与恢复

- 中间仓库/运行时状态：<有效，因为...>
- 兼容性/迁移：<...>
- 功能开关/发布：<...>
- 回滚/恢复：<...>
- 可观测性/审计：<...>

## 允许延后的工作

- <事项 -> 指名的章节；若为空则写 none>

## 未决决策

- 实现之前必须为 `none`，否则阻塞。

## 重规划 / 硬上限触发器

- 验收标准或行为发生变化。
- 公共契约/schema/权限/状态所有者/并发/破坏性/发布语义发生变化。
- 范围实质性扩大。
- base/head 超出被跟踪的实现或修复。

- 五轮完整 `SECTION` 评审仍未出现一次干净的、覆盖完整的评审时，该尝试退役，并由 `[tier: plan]` 子代理触发自动再分解。

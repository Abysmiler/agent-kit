<!-- 中文翻译版；英文原版为本目录同名 .md 文件。若两者不一致，以英文版为准。 -->

# 功能集成评审请求

- Review mode: `INTEGRATION`
- Working path: `<path>`
- Feature: `<name>`
- Feature base: `<commit>`
- Feature head: `<commit>`
- Feature contract: `.agent-work/PLAN-FULL.md`
- Feature state: `.agent-work/FEATURE-STATE.md`
- Section artifacts: `.agent-work/sections/`
- Review index: `.agent-work/reviews/`
- Output: `.agent-work/reviews/FEATURE-INTEGRATION-r01.md`
- Review skill: `code-review`

## 必需关注点

- 原始完整功能目标、非目标与需求覆盖。
- 跨章节 API/schema/状态/权限/顺序/错误契约。
- 端到端的正常、负面与部分失败路径。
- 迁移、兼容性、发布、回滚、功能开关与清理。
- 安全、隐私、可靠性、性能、可观测性与运维。
- 延后工作的收口与分支范围完整性。

## 评审语义

不要机械地逐行重放每个已接受的章节。先对当前集成状态形成独立观点，再使用先前的章节台账核验收口情况并识别证据缺口。报告 `mergeable`（可合并）、`not-mergeable`（不可合并）或 `insufficient-evidence`（证据不足）。

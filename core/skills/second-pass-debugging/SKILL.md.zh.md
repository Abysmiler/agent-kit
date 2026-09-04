<!-- 中文翻译版；英文原版为本目录同名 .md 文件。若两者不一致，以英文版为准。 -->

---
name: second-pass-debugging
description: Use when a previous bug fix attempt did not resolve the issue, the user says the bug still happens, a test still fails after one repair round, Codex is starting a second or later debugging pass, or a debugging session is long/repetitive enough to need persistent state across context compaction. Also use when the user asks for systematic debugging, root-cause debugging, or durable debug notes in .agent-work/debug/. Do not use for the first ordinary bug-fix attempt unless explicitly requested or the session is already becoming long-running.
---

# 第二轮调试与持久化调试（Second Pass And Persistent Debugging）

## 概述

使用本技能来停止反复的"猜-补"式调试。在第二次失败尝试后，或当调试变成长期任务时，回归证据、持久化有用状态、定位根因、做一次最小修复，并验证原始症状。

## 触发纪律

- 当用户说上一次修复无效、同一个测试仍失败、缺陷仍可复现，或一次不成功的尝试之后又开始新一轮调试时，使用本技能。
- 当用户明确要求系统性调试或根因调试时，使用本技能。
- 对于长时间调试、反复实验，或上下文压缩可能丢失重要观察的情形，使用本技能。
- 首次普通缺陷修复不要使用本技能，除非被明确要求，或该工作已明显变成长期任务。

## 持久化调试状态

`.agent-work/debug/` 只用于保存能节省未来工作的调试状态。保持简明且基于证据。

预期结构：

```text
.agent-work/debug/
├── INDEX.md
├── active/
├── unresolved/
└── resolved/
```

`INDEX.md` 应包含三个双列表格：

```md
## Active

| file | summary |
| --- | --- |

## Unresolved

| file | summary |
| --- | --- |

## Resolved

| file | summary |
| --- | --- |
```

- 将当前调查放在 `active/`。
- 将已暂停或仍失败的调查移至 `unresolved/`。
- 将已验证的修复移至 `resolved/`。
- 在每个表格中，`file` 是笔记的相对路径，`summary` 说明未来的代理为何应阅读它。
- 继续同一问题之前，先阅读 `INDEX.md` 以及相关的 `active/` 或 `unresolved/` 笔记。
- 当一次已解决的调试产生可复用的项目知识时，将通用做法记录到相应的项目文档中，例如 `docs/engineering-notes/`。调试笔记本身保留为具体的证据链。

## 工作流

1. **回归证据。**
   - 声明这是一次第二轮（second-pass）调试，且下一步是收集证据。
   - 在 git 仓库中时，用 `git status` 或等价命令检查当前仓库状态。
   - 回顾上一次尝试的修复、被改动的文件、失败的命令、观察到的输出，以及用户关于何处仍失败的报告。
   - 在经代码、diff、日志或测试输出验证之前，将子代理报告、早先的总结和假设视为不可信。

2. **恢复或创建持久化调试状态。**
   - 如果 `.agent-work/debug/INDEX.md` 存在，在重复调查之前先阅读它。
   - 如果这是长期或重复的调查，创建或更新一个 `active/` 笔记并将其加入 `INDEX.md`。
   - 只记录已确认的观察、失败的路径、当前假设、下一步诊断，以及相关命令或手动复现步骤。

3. **复现或保留失败。**
   - 在环境允许时，运行能演示该缺陷的最小命令或手动流程。
   - 在提出修复之前，阅读完整的错误、堆栈跟踪、日志或 UI 症状。
   - 如果问题无法在本地复现，识别缺失的证据并收集诊断信息，而不是猜测。

4. **追溯根因。**
   - 检查近期 diff 与附近可正常工作的示例。
   - 沿着坏数据、错误状态或失败的控制流逆向追溯其源头。
   - 对多组件路径，检查边界：调用方到被调方、UI 到状态、API 到服务、服务到持久化、任务到 worker，或配置到运行时。
   - 优先修复错误行为的源头，而非在症状处添加防护。

5. **与已知的良好模式对比。**
   - 在同一代码库中搜索类似的正常实现。
   - 对比输入、状态所有权、校验、错误处理、异步行为与清理。
   - 如果该模式依赖框架行为或外部 API 且仍有不确定性，对照一手文档或既有的本地示例验证。

6. **形成一个假设。**
   - 写出简明假设："根因似乎是 X，因为证据 Y。"
   - 用尽可能最小的诊断或代码阅读检查来检验假设。
   - 一次只改一个变量；不要堆叠投机性修复。
   - 假设变化时更新活动调试笔记。

7. **新增或确定一个失败的回归面。**
   - 优先添加一个对当前缺陷失败、且验证真实行为的自动化测试。
   - 如果没有测试框架，创建或描述最小的、可重复的手动或脚本复现。
   - 不要添加只执行代码而不验证缺陷行为的断言。

8. **实现最小修复。**
   - 修复已确认的根因。
   - 避免无关重构、大范围重写、新的兼容层或隐藏的回退逻辑。
   - 如果直接修复会恶化本已过大的模块、不清晰的状态所有者、脆弱的状态机或缺乏测试的核心路径，先暂停并说明最小的使能重构，再进行编辑。

9. **先验证，再宣称进展。**
   - 重新运行最初失败的命令或复现步骤。
   - 按改动行为的需要，运行相关测试、类型检查、lint、构建或浏览器验证。
   - 报告确切的命令与结果。如果检查无法运行，说明阻碍以及剩余所需的验证。
   - 如果修复得到验证，将调试笔记从 `active/` 移至 `resolved/` 并更新 `INDEX.md`。
   - 如果工作在验证前停止或问题仍然存在，将笔记移至或保留在 `unresolved/` 下并更新 `INDEX.md`。

10. **反复失败后升级。**
    - 如果本轮失败，带着新结果回到证据收集，而不是再叠一层修复。
    - 同一症状经过三次失败修复后，停止并与用户一起重新评估架构、状态所有权、并发、陈旧假设或测试有效性，然后再尝试其他实现。

## 子代理使用

- 仅将子代理用于有边界、可独立验证的调查，例如追踪调用链、对比相似实现或分诊测试输出。
- 主代理拥有假设、最终修复、diff 审查与验证。
- 不要委托高风险架构、数据删除、迁移、安全决策或发布决策。

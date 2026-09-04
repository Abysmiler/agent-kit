<!-- 中文翻译版；英文原版为本目录同名 .md 文件。若两者不一致，以英文版为准。 -->

---
name: debug-notes-to-engineering-notes
description: Use after a difficult or long debugging session when the user asks to turn .agent-work/debug records, resolved investigations, failed attempts, git history, or version-specific framework/host behavior into reusable docs/engineering-notes. Use when Codex must separate transferable engineering lessons from project-specific implementation notes, document official-doc gaps or contradictions with observed behavior, and make notes sufficient for someone to reproduce a similar capability or diagnose a similar issue without reading the original code. Do not use for actively debugging a live bug unless the task is specifically to archive or synthesize debug knowledge.
---

# 调试笔记转工程笔记（Debug Notes To Engineering Notes）

## 概述

使用本技能将已完成的调试证据转化为持久的工程文档。产出应帮助未来的工程师实现类似能力或诊断类似问题，而无需重读原始代码或重新踩一遍同样的失败路径。

本技能用于调试后的知识提取。对于仍在进行中的反复调试，请先使用项目的第二轮调试（second-pass debugging）工作流，待证据稳定后再使用本技能。

## 工作流

1. **盘点证据。**
   - 当 `.agent-work/debug/INDEX.md` 存在时，阅读它。
   - 阅读 `.agent-work/debug/resolved/`、`.agent-work/debug/unresolved/` 和 `.agent-work/debug/active/` 下的相关文件。
   - 如果用户提到的问题不在调试记录中，先检查 `git log`、相关提交差异、被移动/删除的文档以及附近的历史笔记，再假设证据缺失。
   - 将先前的总结视为线索而非事实。用调试笔记、diff、日志、测试或官方文档加以验证。

2. **对每项发现进行分类。**
   - 将可迁移的工程知识放入 `docs/engineering-notes/`。
   - 将项目专属的实现选择、产品行为、类名、默认值、功能边界、参数 ID、本地调试开关或当前架构放入普通的 `docs/` 文件，例如 `docs/<topic>-implementation-notes.md`。
   - 将具体的调试记录保留在 `.agent-work/debug/` 中作为证据；不要把整段日志复制进工程笔记。

3. **按模块或失败模式拆分笔记。**
   - 为相互独立的事项分别建立笔记，例如坐标系、宿主校验、渲染采样、API 行为、持久化/回写、事件分发或部署状态。
   - 不要把不相关的问题合并成一个巨大的"包罗万象"式笔记。
   - 仅在能避免混淆之处添加交叉链接。

4. **从读者任务视角撰写笔记。**
   - 面向实现同类能力或面对同类缺陷的读者撰写。
   - 不要写产品营销文案或功能走查。
   - 使笔记足以在不阅读实现代码的情况下复现推理过程。
   - 优先记录层契约、数据流边界、失败特征、诊断命令和验证面，而非逐个符号的实现细节。

5. **同时记录成功与失败。**
   - 包含正确的模型或修复模式。
   - 包含失败的路径，并解释每条路径为何错误。
   - 每篇工程笔记以 `Previous Wrong Attempts` 结尾，除非该笔记纯粹是索引或概述。

## 工程笔记的必备结构

`docs/engineering-notes/` 下每篇实质性文件应包含：

- 标题。
- `Last updated: <YYYY-MM-DD HH:MM TZ>`。
- `Reference commit: <完整 git commit 哈希>`。
- 当行为依赖于宿主应用、操作系统、框架、库、SDK、服务、模型或工具版本时，写 `Observed versions: ...`。
- 若涉及外部行为，写官方 API 或文档基线。
- 对官方文档未承诺、或与官方文档相矛盾的行为，记录带版本的观察结果。
- 可复现的层/模块定义：坐标系、状态所有权、数据流、API 边界、生命周期边界，或问题域中的等价物。
- 诊断清单或证据来源。
- 正确的解决方案或修复模式。
- `Previous Wrong Attempts`：解释尝试过什么、为何失败、以及如何识别该失败模式。

## 官方文档规则

- 不要为稳定且文档完善的行为复制官方文档。
- 只记录官方文档遗漏、表述含糊，或对所观察版本表述错误的内容。
- 检查外部行为时使用一手来源：官方文档、SDK 头文件、源代码、changelog、issue 跟踪器，或经核实的本地版本输出。
- 当观察结果与文档不一致时，显式写出区别：
  - "官方文档声明……"
  - "在 <版本> 上观察到……"
  - "这不受官方 API 保证……"
- 如果无法从仓库或环境中发现版本，询问用户或将版本标记为未知。不要把未标版本的宿主行为当作普遍规律。

## 工程笔记与实现笔记的边界

`docs/engineering-notes/` 用于：

- 官方文档未覆盖的框架或宿主行为。
- 调试方法与决策树。
- 失败特征以及如何区分相似失败。
- 跨项目经验、API 注意事项和验证协议。
- 能帮助其他实现的成功与失败路径。

其他 `docs/` 文件用于：

- 当前产品形态。
- 项目专属的功能行为。
- 类、函数、目标或参数的名称。
- 默认值与检视器（inspector）标签。
- 本地调试文件路径或开关。
- 当前实现架构与所有权选择。

如果一篇笔记两者都需要，就拆分它：把可迁移的经验留在 `engineering-notes`，并链接到项目实现笔记以获取局部细节。

## 验证

完成之前：

- 在 `docs/engineering-notes/` 中搜索项目专属名称、本地文件路径、功能默认值、类名、参数 ID 和产品描述。除非它们显式属于对项目外部也有价值的带版本观察，否则将其移出。
- 确认项目专属的实现选择在仍然重要时，已在 `engineering-notes` 之外的 `docs/` 某处被记录。
- 确认每篇工程笔记都有更新的时间戳和参考提交元数据。
- 确认官方文档的空缺与矛盾都附有被观察的版本。
- 运行 `git diff --check`。
- 对于仅涉及文档的改动，通常无需代码测试；说明因改动仅涉及文档而未运行测试。

## 完成报告

在最终回复中列出：

- 新建或更新的工程笔记。
- 在 `engineering-notes` 之外新建或更新的实现笔记文档。
- 使用的证据来源：调试记录、git 提交、官方文档、本地头文件、日志、测试，或用户提供的观察。
- 运行的验证命令及其结果。
- 任何仍未知的版本或证据空缺。

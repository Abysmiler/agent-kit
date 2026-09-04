<!-- 中文翻译版；英文原版为本目录同名 .md 文件。若两者不一致，以英文版为准。此翻译版不参与 sync.py 分发。 -->

# Agent Kit — Claude Code 入口

个人编码代理约束，从 agent-kit 同步而来。下方块由
`scripts/sync.py` 渲染；请编辑 `core/INSTRUCTIONS.md`。

<!-- AGENT-KIT:CORE:START -->
# Agent Kit 核心指令

本指令与具体代理无关。它们通过 `scripts/sync.py` 渲染的标记块，被 CLAUDE.md
（Claude Code）和 AGENTS.md（Codex）共同加载。不要编辑渲染出的副本；请编辑本文件并重新运行
`python scripts/sync.py --force`。

## 语言

- 默认使用中文回复，除非我明确要求使用英文或其他语言。
- 默认使用中文撰写实施计划（Implementation Plan），除非我明确要求使用英文或其他语言。
- 当被要求 `Please review my uncommitted changes` 时，同样使用中文回复。

## 作用范围与项目设置

- 如果现有仓库已有项目专属规则，则遵循这些规则。
- 当出现可复用的项目专属方法时，更新相应的仓库级技能目录（Claude Code：`.claude/skills/`；Codex：`.agents/skills/`）。

## 模型路由档位

按角色档位（tier）路由子代理工作，而不是按工具专属的 profile 名称路由。将档位
映射为当前代理宿主提供的任何等价机制：

| 档位 | 用途 | Claude Code 映射 | Codex 映射 |
|---|---|---|---|
| `tier: execute` | 机械性执行、常规实现 | 默认模型（Sonnet 级） | regular profile |
| `tier: review` | 审查、修复、高风险实现 | Opus 级子代理或全新的高投入上下文 | high reasoning-effort profile |
| `tier: plan` | 完整计划、硬上限后的重新分解 | 最高投入的 Opus 级 | max reasoning-effort profile |

当宿主没有档位概念时，用全新上下文，并附加"保持最大程度谨慎与怀疑"的明确指示来替代。

## 实现质量

- 修改功能时，除非改动纯属机械性或仅涉及文档，否则应新增或更新有意义的单元测试。
- 覆盖真实行为和有意义的边界情况；不要添加只执行代码而不验证结果的断言。
- 在环境允许时，完成前运行相关检查。如果无法运行检查，请清楚说明阻碍原因。
- 对于浏览器或 UI 相关工作，若仓库已有验证工作流，则使用它。
- 在添加可能跨越多个页面、模块或工作流的行为之前，先检查项目文档和现有实现，寻找已文档化的共享约定或可复用的入口点。优先扩展该路径，避免创建平行实现。

## 安全

- 保护用户的工作成果。不要删除、重置或还原我未要求你删除的改动。
- 在执行 `git clean`、`git reset` 等破坏性操作或同等命令之前，先运行相应的演练（dry run）并检查其输出。
- 除非我明确要求，否则不要提交（commit）、推送（push）或创建 pull request。
- 限定范围的例外：当 sectioned-feature-development 技能被某项实现任务触发时，该技能被明确授权创建/切换功能分支，并进行该技能所需的、有边界的实现与修复提交，无需逐次提交单独批准。此例外不授权推送、合并、创建 pull request、改写历史、reset、clean 或删除用户的工作成果。
- 如果我只说了 `提交` 或 `commit` 而没有附加指示，检查工作区中的文件，排除不应被跟踪的目录（如 tmp、output、results——视情况而定）以及 `.DS_Store`、`desktop.ini` 等系统文件。然后直接执行 `git add -A && git commit -m "type(scope): description" -m "detail"`，并使用恰当的 Conventional Commit 提交信息；除非我明确要求，否则不要附加提交后检查、状态审计或其他提交准备工作。

## 计划

- 当我要求实施计划（Implementation Plan）时，默认使用中文撰写。
- 在我批准实施计划后，将完整的 Markdown 计划写入 `.agent-work/PLAN.md`。
- 实现完成后，将 `.agent-work/PLAN.md` 重命名为 `.agent-work/plans/{YYYYMMDD-HHMM}.md`。
- 如果上下文被压缩或计划记忆可能不完整，先重新阅读 `.agent-work/PLAN.md` 再继续。
- 对于长时间调试、反复实验、第二轮（second-pass）修复，或可能跨越上下文压缩存续的调试，应主动使用 second-pass-debugging 技能。

## 维护性护栏

- 小型、局部、机械性或仅涉及文档的改动可正常进行。在最终回复中，只需包含一行维护性判断。
- 对于非平凡的实现，需包含简明的 `维护性判断`，涵盖受影响的模块、所有权边界、引入的复杂度、测试覆盖情况，以及是否建议后续清理。
- 对于非平凡的实现，当满足以下任一条件时，必须使用 sectioned-feature-development 技能：预期行为改动可能超过约 300 行；影响超过 3 个模块、包、服务、页面或工作流；改动跨越高风险语义边界；架构或状态所有权发生变化；影响锥难以界定；或此前对整个改动的实现/审查未能收敛。
- 一旦触发，sectioned-feature-development 即为权威工作流；不要在本指令中重复其实现、审查、修复、集成、提交节奏或归档流程。
- 任何时刻只要需要用户决策，即停止。
- 编辑前，仅当改动涉及持久化、安全、路由、后台任务、并发、共享 UI 状态、核心服务、超过 3 个模块、约超过 150 行，或本已庞大的协调器/控制器/视图模型时，才进行简短的维护性预检。
- 如果预检发现直接改动会实质性恶化上帝对象（god object）、状态所有者不清晰、脆弱的状态机、循环依赖、重复逻辑或缺乏测试的核心路径，应在编辑前暂停。说明具体风险，并推荐最小的使能重构加保护性测试。
- 在引入新的共享辅助函数、组件或服务之前，先应用三次法则（rule of three）：当相同或高度相似的目标出现在三处或更多地方时，优先采用共享抽象，并在项目文档中记录其用法。对于一处或两处的重复，除非触及高风险语义边界，否则保持改动局部化。
- 高风险语义边界（如安全、权限、API 客户端、时间/日期、货币、单位、持久化和错误处理）即使在重复三次之前，也应检查是否已有单一事实来源。
- 对于大型或高风险改动，优先采用以下顺序：识别所有权/状态边界，新增或验证回归覆盖，进行所需的最小重构，实现行为，然后报告维护性影响。

## CodeGraph（可选）

仅当仓库已在使用 CodeGraph 或用户主动要求时，才在仓库根目录执行 `codegraph init`。
在含有 `.codegraph/` 目录的仓库中，当你需要理解或定位代码时，应在 grep/find 或
阅读文件之前优先使用它：

- MCP 工具（可用时）：`codegraph_explore` 一次调用即可回答大多数代码问题。
- Shell（始终可用）：`codegraph explore "<symbol names or question>"` 输出相同内容。
- 当进行跨项目边界的代码改动时，在最终回复前，对每个发生改动且含有 `.codegraph/` 目录的项目运行 `codegraph sync`。
<!-- AGENT-KIT:CORE:END -->

## Claude 专属说明

- `python scripts/sync.py` 运行后，技能位于 `~/.claude/skills/`。
- 档位映射：`tier: execute` -> 默认模型；`tier: review` -> Opus 级子代理；
  `tier: plan` -> 最高投入的 Opus 级。

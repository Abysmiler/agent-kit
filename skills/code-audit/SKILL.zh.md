---
name: code-audit
description: "Perform or continue a periodic whole-system codebase audit covering correctness, architecture, security, data, reliability, operations, supply chain, tests, maintainability, anti-bloat, and AI-agent risks. Use for explicitly requested audits, audit-reminder follow-ups after sustained development, and risk reassessment. Keeps one durable coverage-and-findings file so each cycle deepens instead of rescanning the repository from zero. Not a merge gate for one bounded change; use the code-review skill for that."
---

> 本文件是 `SKILL.md` 的中文译本,仅供人阅读,不参与分发。若有出入,以英文版为准。

# 代码审计

把系统当作一个持续维护的产品来审计,而不是一份 diff。审计是风险抽样:它永远不能证明未审计的区域是安全的。每次运行都有边界,记录覆盖了什么,并给下一次运行留下更好的起点。

## 边界

- 用于周期性或明确请求的全系统审计。针对单个 pull request、提交范围或 diff,使用 `code-review` 技能。
- 优先遵循仓库本地的指令。
- 默认只审计。只有用户授权修复时才改动产品代码。
- 保护用户的工作和历史。绝不 reset、clean、merge、push、部署或触碰生产系统。
- 把以往的审计报告、代理摘要、提交消息和通过的测试当作线索,而不是当前行为的证明。
- 如果这次审计是委派给你的,你就是审计执行者;不要再把同一个审计委派出去。

## 持久状态

```text
.agent-work/audit/
├── AUDIT.md                  # 唯一的持久文件;原地更新
└── runs/{YYYYMMDD-HHMM}.md   # 每次运行一份报告
```

`AUDIT.md` 模板(用英文书写;保持足够短,每次运行都能通读):

```markdown
# Audit State

## Profile
<Optional, 3-8 lines: what the system is for, crown-jewel data and privileged
actions, always-audit surfaces, risk tolerance, exclusions. User-approved
priorities only; mark assumptions as assumptions.>

## System Map
<Brief: entry points and trust boundaries, modules and owners, data stores and
migrations, jobs/queues, external services, build/release path, agent tooling.>

## Coverage
| Domain | Last audited (commit, date) | Depth | Next focus |
|---|---|---|---|
| Authorization | a1b2c3d, 2026-01-15 | deep | export endpoints not traced |
| Data migrations | never | - | restore path, backfill locking |

## Findings
| ID | Severity | Status | Title | Location | Last verified |
|---|---|---|---|---|---|
| AUD-001 | Must Fix | open | Export skips tenant filter | src/export.ts:88 | a1b2c3d |
```

- 领域(Domain)取自 [references/coverage.md](references/coverage.md);只列出适用于本系统的领域。
- 深度(Depth)取 `skim`、`sampled` 或 `deep`。绝不用百分比概括覆盖情况。
- 状态(Status)取 `open`、`fixed`、`accepted` 或 `deferred`。发现的 ID 保持稳定,绝不复用。发现的完整细节保存在提出它的那次运行报告里。

## 工作流程

### 1. 对齐现状

- 记录分支、head 提交和 `git status`。注意用户未提交的改动,并且不要动它们。
- 通读 `AUDIT.md`。如果不存在就创建:根据仓库证据起草 Profile,构建 System Map,并把适用的领域列为 `never`。
- 删除已不存在的地图条目和发现位置。如果地图已不能描述系统(重写、新平台、新的数据或权限模型),重建地图并把受影响的 Coverage 行重置为 `never`,而不是打补丁。
- 记下当前环境中实际可用的检查、扫描器和运行时证据。

### 2. 选择有边界的范围

按以下优先级挑选本次运行的范围;一旦再加内容就无法在一次会话内可信地完成,就停止添加:

1. 自各自 `Last audited` 提交以来发生变化的区域(`git diff --stat <commit>..HEAD`、`git log`),按风险而非行数加权。
2. 从未覆盖或最久未覆盖的最高风险领域,包括 Profile 中点名的任何常审面。
3. 需要对照当前代码重新验证的未关闭发现。

至少包含一条贯穿所选区域的端到端关键工作流。开始前说明范围以及明确排除的内容。只有当优先级或风险容忍度的选择会实质改变范围且无法推断时,才询问用户。

### 3. 发现

针对所选领域阅读 [references/coverage.md](references/coverage.md)。对每个区域:

- 形成具体的失效假设,然后根据代码、配置、历史、测试或运行时证据予以证实或证伪。
- 从入口点追踪关键不变量,贯穿领域逻辑、持久化和副作用;局部正确的函数不能证明整个工作流正确。
- 不要只抽样看起来复杂的文件。要包含入口点、权限关卡、持久化、迁移、后台任务、集成和发布路径。
- 先完成整个范围的发现,再修复任何东西。
- 没有发现的区域记为已覆盖;不要捏造发现。

### 4. 对发现分类

每个发现都需要触发条件(如何到达)、影响、证据(`file:line`、命令输出或复现)以及修复方向。把多个症状归并到一个根因之下。给每个陈述标注是已验证的事实还是推断;未证实的怀疑是缺口,不是发现。

- `Must Fix`:安全、隐私、数据丢失或损坏、严重的不正确、不安全的部署或恢复,或已经阻碍可靠开发的结构性损害。
- `Should Fix`:值得排期处理的真实可靠性、架构、测试、运维或可维护性风险。
- `Needs Decision`:正确结果取决于产品语义、风险容忍度或只有用户能做的取舍。
- `Note`:有边界、可接受的妥协或观察;记录其上限以及什么情况下值得重新审视。

按影响、可能性、波及范围和可逆性排序,而不是按代码规模或扫描器给出的严重级别。当同一类问题跨周期反复出现时,建议采用持久控制手段(测试、lint、共享入口、CI 守卫),而不是再扫描一次。

### 5. 仅在授权时修复

- 只修复用户授权的发现 ID。在选择修复方向之前,先解决阻塞性的 `Needs Decision`。
- 做最小且连贯的改动,并在根因边界处添加回归检查。
- 自己验证每个修复:运行相关检查,并对照发现的触发条件重读修复 diff。只有当闭合在当前代码中可见并有上述证据支持时,才标记为 `fixed`。
- 不要启动重新审计的轮次。如果修复未通过验证或引出新问题,停下来,带着证据把该项作为决策交给用户。

### 6. 记录与报告

- 更新 `AUDIT.md`:System Map 的变化、每个已覆盖领域的提交/日期/深度/下次重点,以及每个发现的状态和最后验证提交。
- 写入 `.agent-work/audit/runs/{YYYYMMDD-HHMM}.md`,默认使用中文,路径、符号、命令和发现 ID 保持原样:

```markdown
# 审计报告 {YYYY-MM-DD HH:MM}

- 范围: <head commit; domains and areas covered; why they were selected>
- 未覆盖: <what was left out and why>
- 证据: <checks run and results; evidence that was unavailable>

## 发现
### AUD-00N <title> — <severity>
- 触发: <how it is reached>
- 影响: <what goes wrong, for whom>
- 证据: <file:line / command output; fact or inference>
- 修复方向: <direction; fix status if remediated>

## 需要用户决策
<Needs Decision items and unresolved fixes, each with options>

## 下次重点
<domains and areas to prioritize next run>
```

- 默认用中文回复用户,简要采用同样的结构:先按严重程度列出发现,然后是需要的决策、覆盖的局限以及下次重点。绝不暗示未审计的区域是安全的。

当范围内每个区域都更新了 Coverage、每个发现都有证据、已授权的修复都经过验证、且报告说明了自身局限时,一次运行才算完成。

## 提交 trailer

除非用户要求,否则不要提交。当用户要求提交一次已完成的审计运行时,在提交消息中恰好包含一次以下 trailer,以便审计提醒钩子重置计数:

```text
Maintenance-Audit: true
```

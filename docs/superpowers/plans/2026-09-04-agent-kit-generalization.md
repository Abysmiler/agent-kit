# agent-kit 通用化重构实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把 AGENTS.md-main（Codex 个人约束仓库）重构为代理无关、Windows 优先跨平台、Claude Code + Codex 双支持的 agent-kit，可直接安装使用。

**Architecture:** core/（INSTRUCTIONS.md 唯一事实来源 + 8 技能 + git-hooks）+ adapters/（codex/claude 双入口，构建式渲染）+ scripts/sync.py（双目标原子分发）。模型路由抽象为三级角色档位；两处文档冲突统一（单次干净准则、worktree 注册表约定）。

**Tech Stack:** Python 3.9+（零第三方依赖，pathlib + argparse + 内联 unittest）、POSIX sh（git hooks，Git Bash 兼容）、Markdown。

**源仓库：** `E:\rpo\AGENTS.md-main\AGENTS.md-main\`（只读，不动）
**目标仓库：** `E:\rpo\AGENTS.md-main\agent-kit\`（新建；注意 agent-kit/docs/ 下已有 spec 与 plan，保留）
**注意：** 源与目标都不是 git 仓库（zip 解压）。所有"Commit"步骤在 Task 1 初始化 git 后执行。Windows 环境，shell 命令用 Git Bash 语法。

---

### Task 1: 初始化 agent-kit 仓库骨架与 git

**Files:**
- Create: `agent-kit/.gitignore`
- Create: `agent-kit/core/`、`agent-kit/adapters/codex/agents/`、`agent-kit/adapters/claude/`、`agent-kit/scripts/`（目录）

- [ ] **Step 1: 初始化 git 仓库**

```bash
cd /e/rpo/AGENTS.md-main/agent-kit && git init -b main
```

Expected: `Initialized empty Git repository`

- [ ] **Step 2: 写 .gitignore**

`agent-kit/.gitignore` 内容：

```gitignore
__pycache__/
*.pyc
.DS_Store
.agent-work/
```

- [ ] **Step 3: 首次提交（docs 已存在的 spec 一并纳入）**

```bash
cd /e/rpo/AGENTS.md-main/agent-kit && git add -A && git commit -m "chore: initialize agent-kit repository with design docs"
```

Expected: commit 成功，包含 docs/superpowers/specs/ 下已有文件

---

### Task 2: 编写 core/INSTRUCTIONS.md（唯一事实来源）

**Files:**
- Create: `agent-kit/core/INSTRUCTIONS.md`

- [ ] **Step 1: 写 core/INSTRUCTIONS.md**

内容如下（基于原 AGENTS.md 手术：删 Docker/colima 段、删飞书、模型档位改三级角色制、`$skill` 改中性写法、CodeGraph 改可选、新增 Routing 段与跨代理说明）：

```markdown
# Agent Kit Core Instructions

These instructions are agent-agnostic. They are loaded by both CLAUDE.md
(Claude Code) and AGENTS.md (Codex) via the marker block rendered by
`scripts/sync.py`. Do not edit the rendered copies; edit this file and re-run
`python scripts/sync.py --force`.

## Language

- Reply in Chinese by default, unless I explicitly ask for English or another language.
- Write Implementation Plans in Chinese by default, unless I explicitly ask for English or another language.
- When asked `Please review my uncommitted changes`, reply also in Chinese.

## Scope And Project Setup

- If an existing repository already has project-specific rules, follow them.
- When a reusable project-specific method emerges, update the relevant repo-level skill directory (for Claude Code: `.claude/skills/`; for Codex: `.agents/skills/`).

## Model Routing Tiers

Route sub-agent work by role tier, not by tool-specific profile names. Map the
tier to whatever the current agent host provides:

| Tier | Use for | Claude Code mapping | Codex mapping |
|---|---|---|---|
| `tier: execute` | mechanical execution, routine implementation | default model (Sonnet-class) | regular profile |
| `tier: review` | review, repair, high-risk implementation | Opus-class subagent or fresh high-effort context | high reasoning-effort profile |
| `tier: plan` | full plans, hard-cap re-decomposition | Opus-class at highest effort | max reasoning-effort profile |

When the host has no tier concept, substitute a fresh context plus explicit
instructions to be maximally careful and skeptical.

## Implementation Quality

- When changing functionality, add or update meaningful unit tests unless the change is purely mechanical or documentation-only.
- Cover real behavior and meaningful edge cases; do not add assertions that only execute code without verifying outcomes.
- Run the relevant checks before finishing when the environment permits it. If checks cannot run, explain the blocker clearly.
- For browser or UI work, use the repository's existing validation workflow when it exists.
- Before adding behavior that may span multiple pages, modules, or workflows, inspect project docs and existing implementations for a documented shared convention or reusable entry point. Prefer extending that path and avoid creating parallel implementations.

## Safety

- Preserve user work. Do not remove, reset, or revert changes I did not ask you to remove.
- Before destructive operations such as `git clean`, `git reset`, or equivalent commands, run the appropriate dry run and inspect the output.
- Do not commit, push, or create pull requests unless I explicitly ask for that action.
- Scoped exception: when the sectioned-feature-development skill is triggered for an implementation task, it is explicitly authorized to create/switch the feature branch and make the bounded implementation and repair commits required by that skill without separate per-commit approval. This exception does not authorize push, merge, pull-request creation, history rewriting, reset, clean, or deletion of user work.
- If I only say `提交` or `commit` without extra instructions, inspect the files in the work space, exclude folders that shouldn't be tracked like tmp, output, results (it depends), and system files like `.DS_Store`, `desktop.ini`. Then execute `git add -A && git commit -m "type(scope): description" -m "detail"` directly with an appropriate Conventional Commit message; do not add post checks, status audits, or other commit preparation unless I explicitly ask for them.

## Plans

- When I ask for an Implementation Plan, write it in Chinese by default.
- After I approve an Implementation Plan, write the complete Markdown plan to `.agent-work/PLAN.md`.
- When the implementation is complete, rename `.agent-work/PLAN.md` to `.agent-work/plans/{YYYYMMDD-HHMM}.md`.
- If context is compacted or plan memory may be incomplete, reread `.agent-work/PLAN.md` before continuing.
- For long debugging sessions, repeated experiments, second-pass fixes, or debugging likely to survive context compaction, proactively use the second-pass-debugging skill.

## Maintainability Guardrails

- Small, local, mechanical, or documentation-only changes should proceed normally. In the final response, include only a one-line maintainability judgment.
- For non-trivial implementations, include a concise `维护性判断` covering affected modules, ownership boundaries, complexity introduced, test coverage, and whether follow-up cleanup is recommended.
- For a non-trivial implementation, must use the sectioned-feature-development skill when any of the following applies: expected behavioral edits may exceed roughly 300 lines; more than 3 modules, packages, services, pages, or workflows are affected; the change crosses a high-risk semantic boundary; architecture or state ownership changes; the impact cone is difficult to bound; or a previous whole-change implementation/review failed to converge.
- When triggered, sectioned-feature-development is the authoritative workflow; do not duplicate its implementation, review, repair, integration, commit-cadence, or archival procedure in these instructions.
- Stop any time when user decision is needed.
- Before editing, do a brief maintainability preflight only when the change touches persistence, security, routing, background jobs, concurrency, shared UI state, core services, more than 3 modules, roughly more than 150 lines, or an already-large coordinator/controller/view model.
- If the preflight finds that a direct change would materially worsen a god object, unclear state owner, fragile state machine, circular dependency, duplicated logic, or under-tested core path, pause before editing. Explain the specific risk and recommend the smallest enabling refactor plus protective tests.
- Apply the rule of three before introducing new shared helpers, components, or services: when the same or closely similar goal appears in three or more places, prefer a shared abstraction and document its use in the project docs. For one-off or two-place duplication, keep the change local unless it affects a high-risk semantic boundary.
- High-risk semantic boundaries, such as security, permissions, API clients, time/date, money, units, persistence, and error handling, should be checked for an existing single source of truth even before three repetitions.
- Prefer this sequence for large or risky changes: identify ownership/state boundary, add or verify regression coverage, make the smallest needed refactor, implement the behavior, then report maintainability impact.

## CodeGraph (optional)

Execute `codegraph init` at the repo root only when the repository already uses
CodeGraph or the user asks for it. In repositories with a `.codegraph/`
directory, reach for it BEFORE grep/find or reading files when you need to
understand or locate code:

- MCP tool (when available): `codegraph_explore` answers most code questions in one call.
- Shell (always works): `codegraph explore "<symbol names or question>"` prints the same output.
- When making code changes across project boundaries, run `codegraph sync` in every changed project that has a `.codegraph/` directory before the final response.
```

- [ ] **Step 2: 提交**

```bash
cd /e/rpo/AGENTS.md-main/agent-kit && git add core/INSTRUCTIONS.md && git commit -m "feat(core): add agent-agnostic core instructions"
```

---

### Task 3: 迁移 8 个技能目录并删除 openai.yaml

**Files:**
- Create: `agent-kit/core/skills/{sectioned-feature-development,code-review,code-audit,second-pass-debugging,debug-notes-to-engineering-notes,grill-me,init-project,manual-git-worktrees}/`
- Delete: 各技能的 `agents/openai.yaml`（迁移时不复制）

- [ ] **Step 1: 批量复制技能目录（排除 agents/ 子目录与 feishu）**

```bash
cd /e/rpo/AGENTS.md-main
for s in sectioned-feature-development code-review code-audit second-pass-debugging debug-notes-to-engineering-notes grill-me manual-git-worktrees; do
  mkdir -p "agent-kit/core/skills/$s"
  cp -r "AGENTS.md-main/skills/$s/." "agent-kit/core/skills/$s/"
  rm -rf "agent-kit/core/skills/$s/agents"
done
```

Expected: `agent-kit/core/skills/` 下 7 个目录（init-project 在 Task 6 重写，暂不迁移）

- [ ] **Step 2: 验证迁移完整性**

```bash
diff -rq AGENTS.md-main/skills/manual-git-worktrees agent-kit/core/skills/manual-git-worktrees
```

Expected: 仅 `agents` 目录差异（已排除），无文件缺失

- [ ] **Step 3: 提交**

```bash
cd /e/rpo/AGENTS.md-main/agent-kit && git add -A && git commit -m "feat(skills): migrate 7 skills verbatim (agents/openai.yaml excluded)"
```

---

### Task 4: 技能通用化手术（收敛准则、sol_*、私人路径、worktree 统一）

这是内容手术任务。对 `agent-kit/core/skills/` 下已迁移文件做精确编辑。

**Files:**
- Modify: `core/skills/sectioned-feature-development/SKILL.md`
- Modify: `core/skills/sectioned-feature-development/references/{integration-and-convergence.md,orchestration-protocol.md,section-planning.md,artifact-schemas.md}`
- Modify: `core/skills/sectioned-feature-development/assets/{HARD-CAP-REPLAN.template.md,SECTION-CONTRACT.template.md}`
- Modify: `core/skills/code-review/SKILL.md`、`core/skills/code-review/references/section-review-protocol.md`
- Modify: `core/skills/code-audit/references/anti-bloat.md`
- Modify: `core/skills/second-pass-debugging/SKILL.md`、`core/skills/debug-notes-to-engineering-notes/SKILL.md`（如有 `$` 语法）

- [ ] **Step 1: SFD 收敛准则统一为"单次干净"**

`core/skills/sectioned-feature-development/SKILL.md` 逐处修改：

1. 第 8 行（Overview）："A section is provisionally accepted only after two consecutive fresh full `SECTION` reviews find no new material actionable issue." → "A section is provisionally accepted when a fresh, coverage-complete full `SECTION` review finds no new material actionable issue; after a repair, one clean review of the repair delta plus its impact cone is sufficient unless a reset trigger fires."

2. 第 239-242 行（Phase 5 循环）：
```text
4. If there is **no new material actionable finding**:
   - mark the section `section-accepted`. A single coverage-complete clean review is sufficient.
```
（删除 clean_streak == 2 判断；保留 `clean_streak` 变量仅用于 FEATURE-STATE 记录，接受条件改为单次干净）

3. 第 260 行（硬帽）："if the section has not reached two consecutive clean full reviews" → "if the section has not reached a clean, coverage-complete full review"

4. 第 366 行（Non-negotiable rules）："Two consecutive clean full reviews are required for section acceptance." → "One coverage-complete clean full review is required for section acceptance; after repair, a clean review of the repair delta plus impact cone suffices unless a reset trigger fires."

5. 状态机图（第 83 行）`-> CLEAN -> FULL_SECTION_REVIEW` 改为 `-> CLEAN -> SECTION_ACCEPTED`

同步修改 `references/integration-and-convergence.md`（第 29、47、68 行）、`references/orchestration-protocol.md`（第 41、119 行）、`references/section-planning.md`（第 249 行）、`assets/SECTION-CONTRACT.template.md`（第 17、80 行）、`assets/HARD-CAP-REPLAN.template.md`（第 14 行）——所有 "two consecutive clean" / "2 consecutive clean full SECTION reviews" 改为对应的单次干净表述。

- [ ] **Step 2: sol_* 引用改 tier 标记**

全部 7 个文件中的 sol_* 引用（38 处）按映射替换：
- `[@sol_medium](subagent://sol_medium)` → `[tier: execute] subagent`
- `[@sol_high](subagent://sol_high)` → `[tier: review] subagent`
- `[@sol_xhigh](subagent://sol_xhigh)` → `[tier: review] subagent (fresh reviewer context)`
- `[@sol_max](subagent://sol_max)` → `[tier: plan] subagent`
- 裸 `sol_medium`/`sol_xhigh` 等文中提及 → `tier: execute`/`tier: review` 等
- `profile sol_max` 类括号 → `(tier: plan)`

在 SKILL.md Phase 4 的 routing 段（原第 192-197 行）改为：

```markdown
Default routing by role tier (map to the host's available sub-agent tiers, see
core instructions "Model Routing Tiers"):

- ordinary implementation: `[tier: execute]` subagent;
- high-risk implementation or repair: `[tier: review]` subagent;
- section review: fresh `[tier: review]` subagent (reviewer context);
- hard-cap section re-decomposition: `[tier: plan]` subagent.
```

- [ ] **Step 3: worktree 约定统一**

`core/skills/sectioned-feature-development/SKILL.md`：
- 第 273 行 `codex/backup/{feature-slug}-...` → `agent-kit/backup/{feature-slug}-...`
- 第 320-322、372 行的 retry worktree 表述后追加一句："Create retry worktrees under the repository-root `.worktrees/` workspace and register the retry task in `.worktrees/current-agents/` per the manual-git-worktrees skill."
- 第 335 行 Parallelize 段追加："Parallel worktrees must follow the `.worktrees/current-agents/` registry conflict-check protocol (see manual-git-worktrees skill)."

`core/skills/manual-git-worktrees/SKILL.md` 末尾追加一节：

```markdown
## Relationship to sectioned-feature-development

This skill owns the ONLY worktree convention in agent-kit. The
sectioned-feature-development workflow creates its retry and parallel-section
worktrees under the same `.worktrees/` workspace and registers every active
task in `.worktrees/current-agents/` using this skill's conflict-check
protocol. When both are active, the registry is the single source of truth
for scope conflicts.
```

- [ ] **Step 4: 私人路径清除**

- `core/skills/code-audit/references/anti-bloat.md` 第 7-8 行：删除两处 `/Users/ibobby/...` 引用，改为通用表述："Derive this focus from the repository's own largest existing skills and their review/audit conventions."（保留其余内容）
- `core/skills/code-review/SKILL.md` 第 222 行与 code-audit 第 251 行：`{user home dir}/.codex/skills/...` → `{agent host skills directory}/...`

- [ ] **Step 5: `$skill` 语法中性化**

全技能目录：`$code-review` → `code-review skill`、`$code-audit` → `code-audit skill`、`$sectioned-feature-development` → `sectioned-feature-development skill` 等（保留反引号代码格式）。注意 SFD SKILL.md 第 212 行 packet 模板内 `Use: $code-review` 改为 `Use: the code-review skill`。

- [ ] **Step 6: 验证手术完整性**

```bash
cd /e/rpo/AGENTS.md-main/agent-kit
grep -rn "sol_" core/skills/ ; grep -rn "two consecutive\|2 consecutive" core/skills/ ; grep -rn "/Users/" core/skills/ ; grep -rn '\$code-review\|\$code-audit\|\$second-pass' core/skills/
```

Expected: 全部无输出（退出码非 0）

- [ ] **Step 7: 提交**

```bash
git add -A && git commit -m "refactor(skills): unify convergence rule, tier routing, worktree registry, remove private paths"
```

---

### Task 5: 迁移 git-hooks 与安装脚本

**Files:**
- Create: `agent-kit/core/git-hooks/`（6 个 hook + install 脚本，从 `.githooks/` 迁移）

- [ ] **Step 1: 复制 hook 文件**

```bash
cd /e/rpo/AGENTS.md-main
mkdir -p agent-kit/core/git-hooks
cp AGENTS.md-main/.githooks/* agent-kit/core/git-hooks/
cp AGENTS.md-main/scripts/install-git-hooks.sh agent-kit/core/git-hooks/
```

- [ ] **Step 2: 增强 install 脚本（执行位修复）**

`agent-kit/core/git-hooks/install-git-hooks.sh` 在 `git config` 前插入：

```sh
# Windows/zip checkouts can lose the executable bit; restore it when chmod exists.
if command -v chmod >/dev/null 2>&1; then
  chmod +x "$repo_root/.githooks"/* 2>/dev/null || true
fi
```

（最终脚本：`set -eu`；`repo_root=$(git rev-parse --show-toplevel)`；校验 `.githooks` 存在；上述 chmod 块；`git config --local core.hooksPath .githooks`；成功提示。注意：init-project 技能会把此目录复制为项目内 `.githooks/`，所以路径检测用 `.githooks` 不变。）

- [ ] **Step 3: 提交**

```bash
cd /e/rpo/AGENTS.md-main/agent-kit && git add -A && git commit -m "feat(git-hooks): migrate hooks with executable-bit restore for zip checkouts"
```

---

### Task 6: 重写 init-project 技能（双代理版）

**Files:**
- Create: `agent-kit/core/skills/init-project/SKILL.md`
- Create: `agent-kit/core/skills/init-project/references/agent-locations.md`
- 不迁移：原 `scripts/init_codex_project.py`、`assets/WORKFLOW.linear.template.md`、`references/codex-official-locations.md`（Linear/ Symphony 编排是 Codex 私人工作流，YAGNI 删除）

- [ ] **Step 1: 写 SKILL.md**

```markdown
---
name: init-project
description: Initialize or retrofit a repository with agent-native workflow files for Claude Code and/or Codex. Use when the user asks to set up, bootstrap, or dry-run project-level agent configuration, including CLAUDE.md, AGENTS.md, project-level skills directories, and optional git-hook maintainability audit reminders.
---

# Init Project

## Overview

Initialize a repository with agent-native project guidance for whichever coding
agents the user actually uses. Detect the active agent host first, then
generate only the files that host needs. Keep global instructions lean; derive
project guidance at runtime from inspected facts and user decisions.

## Workflow

1. Detect the agent context before proposing files.
   - Active host signals: environment variable `CLAUDECODE=1` or an existing
     `CLAUDE.md` indicates Claude Code; `~/.codex` or an existing `AGENTS.md`
     indicates Codex. A repository may target both.
   - Ask the user only when signals are ambiguous or the repo targets a host
     that is not currently running.
2. Inspect the repository before proposing files.
   - Read `package.json`/`pyproject.toml`/equivalent manifests, existing
     `CLAUDE.md`/`AGENTS.md`, existing project skills directories
     (`.claude/skills/`, `.agents/skills/`), and `docs/README.md` when they exist.
3. Ask only for missing decisions that affect generated files.
   - Technology stack and execution model: frameworks, package manager,
     runtime, Docker or local.
   - Documentation preference, language/style policies for code, UI copy,
     comments, docs, and commit messages. Inspect enough to propose concrete
     policies instead of recording generic "match existing".
   - UI localization policy when applicable.
   - Whether to opt into git-hook maintainability audit reminders, and the
     interval as a commit count (not days/weeks).
   - Whether to use the explicit audit marker trailer `Maintenance-Audit: true`.
4. Generate project guidance directly as the agent.
   - Claude Code targets: `CLAUDE.md` (long-lived rules), `.claude/skills/<project-skill>/SKILL.md` (reusable workflow detail).
   - Codex targets: `AGENTS.md` (long-lived rules), `.agents/skills/<project-skill>/SKILL.md`.
   - When both hosts are targeted, generate both file sets with identical
     rule content; note in each file that the other exists so they stay in sync.
   - Show or explain proposed changes before overwriting existing guidance.
5. Git-hook audit reminders (host-agnostic, lives in the repository).
   - When opted in, copy the agent-kit `core/git-hooks/` package into the
     repository as `.githooks/` plus `scripts/install-git-hooks.sh`, then have
     the user run the installer (Git Bash on Windows).
   - Record cadence with `git config --local agentkit.maintainabilityAuditInterval <N>`
     and, when HEAD exists and the user did not request marker-only baselines,
     `git config --local agentkit.maintainabilityAuditBaseline <head-sha>`.
   - The hook prints a non-blocking reminder: before the interval,
     `建议<N>次后进行项目审计。`; once reached, `上次审计是<N>次前，建议尽快安排审计。`
6. Preserve existing user work.
   - Never overwrite existing files without showing the diff first.
   - Merge with existing project guidance where practical.

## Project Information To Capture

Capture only facts stable and useful across future sessions: languages,
frameworks, package manager, runtime, Docker or local-first; explicit language
and style policies; required test/lint/typecheck/build/migration commands;
documentation preferences; UI localization policy; deployment providers;
safety-sensitive areas (migrations, permissions, auth, destructive ops);
maintainability audit policy.

Do not duplicate agent-host platform capabilities. See
[references/agent-locations.md](references/agent-locations.md) for official
file locations per host.

## Validation

- After generating files, verify: each generated `SKILL.md` has valid
  frontmatter (`name`, `description` only); referenced paths exist;
  `git config --local agentkit.maintainabilityAuditInterval` is set when the
  hook was opted in.
```

- [ ] **Step 2: 写 references/agent-locations.md**

```markdown
# Official File Locations Per Agent Host

Avoid inventing parallel conventions; write to the locations each host reads.

## Claude Code

- User-level instructions: `~/.claude/CLAUDE.md`
- Project-level instructions: `CLAUDE.md` at repository root (auto-loaded)
- Project skills: `.claude/skills/<name>/SKILL.md`
- User-level skills: `~/.claude/skills/<name>/SKILL.md`

## Codex

- User-level instructions: `~/.codex/AGENTS.md` (GUI: Settings - Personalization - Custom instructions)
- Project-level instructions: `AGENTS.md` at repository root
- Project skills: `.agents/skills/<name>/SKILL.md`
- User-level skills: `~/.codex/skills/<name>/SKILL.md`

## Shared (host-agnostic)

- Working state: `.agent-work/` (plans, section artifacts, debug notes, audit ledgers)
- Worktree workspace: `.worktrees/` with `.worktrees/current-agents/` registry
- Git hooks: `.githooks/` + repository-local `core.hooksPath`
```

- [ ] **Step 3: 同步更新 hook 配置键名**

`agent-kit/core/git-hooks/codex-maintainability-audit-reminder` 中两处配置键：
- `codex.maintainabilityAuditInterval` → `agentkit.maintainabilityAuditInterval`
- `codex.maintainabilityAuditBaseline` → `agentkit.maintainabilityAuditBaseline`

（向后兼容读取：先读 `agentkit.*`，无则回退读 `codex.*`，都不存在则退出——保持对原仓库用户的兼容。）

- [ ] **Step 4: 提交**

```bash
cd /e/rpo/AGENTS.md-main/agent-kit && git add -A && git commit -m "feat(skills): rewrite init-project as dual-agent bootstrap with agentkit config keys"
```

---

### Task 7: 迁移 section_plan.py 并跑通其测试

**Files:**
- Create: `agent-kit/scripts/section_plan.py`（从 `core/skills/sectioned-feature-development/scripts/section_plan.py` 复制到顶层 scripts/，技能内保留原位副本）

- [ ] **Step 1: 复制脚本**

```bash
cp agent-kit/core/skills/sectioned-feature-development/scripts/section_plan.py agent-kit/scripts/section_plan.py
```

- [ ] **Step 2: 运行其内联测试**

```bash
cd /e/rpo/AGENTS.md-main/agent-kit && python scripts/section_plan.py test
```

（若原脚本测试不是 `test` 子命令而是直接 `python -u` 运行 unittest，则：`python -m unittest scripts/section_plan -v`；以脚本内 `if __name__ == "__main__"` 实际逻辑为准。）

Expected: 全部测试 PASS（零依赖迁移）

- [ ] **Step 3: 提交**

```bash
git add -A && git commit -m "chore(scripts): hoist section_plan.py to top-level scripts with passing tests"
```

---

### Task 8: sync.py 双目标分发脚本（TDD）

**Files:**
- Create: `agent-kit/scripts/sync.py`
- Test: 内联 unittest（`python scripts/sync.py test` 或 `python -m unittest scripts.sync -v`）

- [ ] **Step 1: 写失败测试**

在 `agent-kit/scripts/sync.py` 中先写测试框架与测试用例（文件顶部为 `render_core_block` 等纯函数测试；复制/分发函数通过临时目录测试）：

```python
class TestRenderCoreBlock(unittest.TestCase):
    def test_renders_core_into_marker_block(self):
        adapter = "# Entry\n\n<!-- AGENT-KIT:CORE:START -->\nold\n<!-- AGENT-KIT:CORE:END -->\n\nTail\n"
        result = render_core_block(adapter, "NEW CORE")
        self.assertIn("<!-- AGENT-KIT:CORE:START -->", result)
        self.assertIn("NEW CORE", result)
        self.assertNotIn("old", result)
        self.assertTrue(result.startswith("# Entry"))
        self.assertTrue(result.endswith("Tail\n"))

    def test_creates_marker_block_when_missing(self):
        adapter = "# Entry only\n"
        result = render_core_block(adapter, "CORE")
        self.assertIn("<!-- AGENT-KIT:CORE:START -->\nCORE\n<!-- AGENT-KIT:CORE:END -->", result)

    def test_preserves_content_outside_block(self):
        adapter = "Head\n\n<!-- AGENT-KIT:CORE:START -->\nx\n<!-- AGENT-KIT:CORE:END -->\n\nTail"
        result = render_core_block(adapter, "y")
        self.assertEqual(result, "Head\n\n<!-- AGENT-KIT:CORE:START -->\ny\n<!-- AGENT-KIT:CORE:END -->\n\nTail")


class TestSyncTargets(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmp.name) / "repo"
        (self.repo / "core" / "skills" / "demo").mkdir(parents=True)
        (self.repo / "core" / "skills" / "demo" / "SKILL.md").write_text("x", encoding="utf-8")
        (self.repo / "core" / "INSTRUCTIONS.md").write_text("CORE", encoding="utf-8")
        (self.repo / "adapters" / "codex" / "AGENTS.md").write_text("# Codex\n\n<!-- AGENT-KIT:CORE:START -->\nold\n<!-- AGENT-KIT:CORE:END -->\n", parents=True)
        (self.repo / "adapters" / "claude" / "CLAUDE.md").write_text("# Claude\n\n<!-- AGENT-KIT:CORE:START -->\nold\n<!-- AGENT-KIT:CORE:END -->\n", parents=True)

    def tearDown(self):
        self.tmp.cleanup()

    def test_sync_codex_target(self):
        home = Path(self.tmp.name) / "codex-home"
        synced = sync_all(self.repo, claude_home=home.with_name("claude-home"), codex_home=home, dry_run=False)
        self.assertTrue((home / "AGENTS.md").read_text(encoding="utf-8").count("CORE") >= 1)
        self.assertTrue((home / "skills" / "demo" / "SKILL.md").exists())
        self.assertIn("Codex", (home / "AGENTS.md").read_text(encoding="utf-8"))

    def test_dry_run_touches_nothing(self):
        home = Path(self.tmp.name) / "codex-home2"
        sync_all(self.repo, claude_home=home, codex_home=home, dry_run=True)
        self.assertFalse(home.exists())
```

- [ ] **Step 2: 运行验证失败**

```bash
cd /e/rpo/AGENTS.md-main/agent-kit && python -m unittest scripts.sync -v 2>&1 | head -20
```

Expected: FAIL/ERROR（render_core_block 未定义）

- [ ] **Step 3: 实现 sync.py**

完整实现要点（继承原 sync_codex_config.py 的原子替换设计）：

```python
#!/usr/bin/env python3
"""Sync agent-kit core instructions and skills into agent host homes."""
from __future__ import annotations
import argparse, os, shutil, subprocess, sys, tempfile, unittest
from pathlib import Path

CORE_START = "<!-- AGENT-KIT:CORE:START -->"
CORE_END = "<!-- AGENT-KIT:CORE:END -->"
IGNORED_COPY_PATTERNS = shutil.ignore_patterns(".DS_Store", "__pycache__", "*.pyc")

class SyncError(RuntimeError): ...

def render_core_block(adapter_text: str, core_text: str) -> str:
    block = f"{CORE_START}\n{core_text.rstrip()}\n{CORE_END}"
    if CORE_START in adapter_text and CORE_END in adapter_text:
        before, rest = adapter_text.split(CORE_START, 1)
        _, after = rest.split(CORE_END, 1)
        return f"{before}{block}{after}"
    return f"{adapter_text.rstrip()}\n\n{block}\n" if adapter_text.strip() else f"{block}\n"

# remove_existing / replace_file / replace_directory：与原 sync_codex_config.py 相同实现
# sync_adapter(repo, adapter_rel, entry_rel, home, dry_run)：渲染 core 进 adapters/<x>/<entry> 的标记区块（写回 repo 内文件，保持 adapter 是构建产物）+ replace_file 到 home/<entry>
# sync_skills(repo, home, dry_run)：core/skills/* → home/skills/*（replace_directory）
# sync_all(repo, codex_home, claude_home, dry_run, target)：按 target 分发 codex/claude/all
# CLI：--target {codex,claude,all} 默认 all、--dry-run、--force、--repo、--codex-home、--claude-home
# git pull --ff-only 逻辑保留（与原脚本一致，非 git 仓库或 pull 失败时 --force 仍可同步）
```

- [ ] **Step 4: 运行验证通过**

```bash
python -m unittest scripts.sync -v
```

Expected: 全部 PASS

- [ ] **Step 5: 实际执行一次分发验证（--dry-run 先行）**

```bash
python scripts/sync.py --dry-run
python scripts/sync.py --force --codex-home /tmp/fake-codex --claude-home /tmp/fake-claude
cat /tmp/fake-codex/AGENTS.md | head -5
```

Expected: dry-run 无写入；force 后两个假 home 下有 AGENTS.md/CLAUDE.md（含渲染的 core）与 skills/demo 等

- [ ] **Step 6: 提交**

```bash
git add -A && git commit -m "feat(scripts): add dual-target sync.py with marker-block rendering and atomic replace"
```

---

### Task 9: adapters 入口文件与修正后的 agents toml

**Files:**
- Create: `agent-kit/adapters/claude/CLAUDE.md`
- Create: `agent-kit/adapters/codex/AGENTS.md`
- Create: `agent-kit/adapters/codex/agents/{tier-execute,tier-review,tier-plan}.toml`（三档，修正名实不符）

- [ ] **Step 1: 写 claude/CLAUDE.md 模板**

```markdown
# Agent Kit — Claude Code Entry

Personal coding-agent constraints, synced from agent-kit. The block below is
rendered by `scripts/sync.py`; edit `core/INSTRUCTIONS.md` instead.

<!-- AGENT-KIT:CORE:START -->
(pending first sync)
<!-- AGENT-KIT:CORE:END -->

## Claude-specific notes

- Skills live in `~/.claude/skills/` after `python scripts/sync.py` runs.
- Tier mapping: `tier: execute` -> default model; `tier: review` -> Opus-class
  subagent; `tier: plan` -> Opus-class at highest effort.
```

- [ ] **Step 2: 写 codex/AGENTS.md 模板**

```markdown
# Agent Kit — Codex Entry

Personal coding-agent constraints, synced from agent-kit. The block below is
rendered by `scripts/sync.py`; edit `core/INSTRUCTIONS.md` instead.

<!-- AGENT-KIT:CORE:START -->
(pending first sync)
<!-- AGENT-KIT:CORE:END -->

## Codex-specific notes

- Skills live in `~/.codex/skills/` after `python scripts/sync.py` runs.
- Tier mapping: `tier: execute` -> regular profile; `tier: review` ->
  `tier-review` profile (high reasoning effort); `tier: plan` -> `tier-plan`
  profile (max reasoning effort). See `adapters/codex/agents/*.toml`.
```

- [ ] **Step 3: 写修正后的三个 toml**

`adapters/codex/agents/tier-execute.toml`：
```toml
name = "tier-execute"
description = "Routine implementation tier for agent-kit workflows"
model = "gpt-5.6-sol"
model_reasoning_effort = "medium"

developer_instructions = """
"""
```

`adapters/codex/agents/tier-review.toml`：
```toml
name = "tier-review"
description = "Review, repair, and high-risk implementation tier for agent-kit workflows"
model = "gpt-5.6-sol"
model_reasoning_effort = "xhigh"

developer_instructions = """
"""
```

`adapters/codex/agents/tier-plan.toml`：
```toml
name = "tier-plan"
description = "Full-plan and hard-cap re-decomposition tier for agent-kit workflows"
model = "gpt-5.6-sol"
model_reasoning_effort = "max"

developer_instructions = """
"""
```

（原 sol_high 名实不符问题通过三档重命名根治；模型名保留 gpt-5.6-sol 但在 README 注明按需替换。）

- [ ] **Step 4: 执行真实 sync 渲染**

```bash
cd /e/rpo/AGENTS.md-main/agent-kit && python scripts/sync.py --force
```

Expected: adapters 两个入口文件的标记区块被渲染为 core/INSTRUCTIONS.md 全文

- [ ] **Step 5: 验证渲染一致性**

```bash
python - <<'EOF'
from pathlib import Path
import sys
sys.path.insert(0, "scripts")
from sync import CORE_START, CORE_END
core = Path("core/INSTRUCTIONS.md").read_text(encoding="utf-8")
for p in ["adapters/codex/AGENTS.md", "adapters/claude/CLAUDE.md"]:
    t = Path(p).read_text(encoding="utf-8")
    rendered = t.split(CORE_START, 1)[1].rsplit(CORE_END, 1)[0]
    assert rendered.strip() == core.strip(), p
print("rendered blocks match core")
EOF
```

Expected: `rendered blocks match core`

- [ ] **Step 6: 提交**

```bash
git add -A && git commit -m "feat(adapters): add claude/codex entries and corrected three-tier codex profiles"
```

---

### Task 10: README 与最终验证

**Files:**
- Create: `agent-kit/README.md`

- [ ] **Step 1: 写 README.md（中文）**

结构（内容按实际产出填写）：
```markdown
# agent-kit

代理无关的编码代理约束套件：一份核心规则 + 8 个技能 + git 审计提醒钩子，
同时支持 Claude Code 与 Codex。

## 快速开始
1. `python scripts/sync.py` — 分发 core 到 ~/.claude 与 ~/.codex（或 `--target claude` 只装 Claude）
2. 新项目用 init-project 技能初始化项目级配置与 git hooks

## 目录结构（core / adapters / scripts）
## 能力地图（8 技能一览表：用途 + 触发条件）
## 模型档位（tier: execute/review/plan 与两代理映射）
## Git Hook 审计提醒（安装、配置键 agentkit.maintainabilityAuditInterval、Maintenance-Audit: true 标记）
## 设计来源（基于 AGENTS.md-main 重构；冲突统一与通用化说明）
```

- [ ] **Step 2: 最终全量验证**

```bash
cd /e/rpo/AGENTS.md-main/agent-kit
python -m unittest scripts.sync -v
python scripts/section_plan.py 2>&1 | head -5   # 或其测试入口，确认可运行
grep -rn "sol_\|two consecutive\|/Users/\|colima\|docker-compose\|feishu" --include="*.md" --include="*.py" --include="*.toml" . | grep -v docs/superpowers || echo "CLEAN"
ls core/skills/ | wc -l    # Expected: 8
```

Expected: 测试全 PASS；grep 输出 CLEAN；技能数 8

- [ ] **Step 3: 提交**

```bash
git add -A && git commit -m "docs: add Chinese README with install guide and capability map"
```

---

## 自审记录（Self-Review）

1. **Spec 覆盖**：设计文档 11 项决策全部有对应 Task——双代理（T6/T9）、8 技能（T3/T6）、tier 抽象（T2/T4/T9）、Windows 跨平台（T5/T8）、子目录位置（T1）、语言策略（T2/T10）、冲突统一（T4）、双目标分发（T8）、hooks 保留（T5/T6）、保留深度（T3 全量迁移）、init 重写（T6）。无缺口。
2. **占位符扫描**：Task 8 Step 3 的实现要点是提纲式（标注"与原脚本相同实现"），这是有意引用既有代码而非占位——原文件在源仓库 `sync_codex_config.py`，完整可抄。其余任务均含完整内容。
3. **类型一致性**：`render_core_block`/`sync_all` 签名在测试与实现提纲间一致（`sync_all(repo, codex_home, claude_home, dry_run, target)`）；配置键名统一为 `agentkit.maintainabilityAudit*`（T6 定义、T5 hook 读取，先后顺序上 T6 Step 3 同步改 hook，一致）。
4. **顺序依赖**：T8 依赖 T2（core 文件）与 T3（skills 目录）；T9 Step 4 依赖 T8。任务已按依赖排序。
```

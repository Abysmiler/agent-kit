---
name: code-audit
description: "Perform or continue a periodic whole-system codebase audit covering correctness, architecture, security, data, reliability, operations, supply chain, tests, maintainability, anti-bloat, and AI-agent risks. Use for explicitly requested audits, audit-reminder follow-ups after sustained development, and risk reassessment. Keeps one durable coverage-and-findings file so each cycle deepens instead of rescanning the repository from zero. Not a merge gate for one bounded change; use the code-review skill for that."
---

# Code Audit

Audit the system as a maintained product, not a diff. An audit is risk sampling: it never proves unaudited areas are safe. Each run is bounded, records what it covered, and leaves the next run a better starting point.

## Boundary

- Use for periodic or explicitly requested whole-system audits. For one pull request, commit range, or diff, use the `code-review` skill.
- Follow repository-local instructions first.
- Audit only by default. Change product code only when the user authorizes remediation.
- Preserve user work and history. Never reset, clean, merge, push, deploy, or touch production systems.
- Treat previous audit reports, agent summaries, commit messages, and passing tests as leads, not proof of current behavior.
- If you were delegated this audit, you are the audit executor; do not delegate the same audit again.

## Persistent state

```text
.agent-work/audit/
├── AUDIT.md                  # the only durable file; update in place
└── runs/{YYYYMMDD-HHMM}.md   # one report per run
```

`AUDIT.md` template (write it in English; keep it short enough to read in full every run):

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

- Domains come from [references/coverage.md](references/coverage.md); list only those that apply to this system.
- Depth is `skim`, `sampled`, or `deep`. Never summarize coverage as a percentage.
- Status is `open`, `fixed`, `accepted`, or `deferred`. Finding IDs are stable and never reused. Full finding detail lives in the run report that raised it.

## Workflow

### 1. Reconcile

- Record branch, head commit, and `git status`. Note uncommitted user changes and leave them alone.
- Read `AUDIT.md` in full. If it is missing, create it: draft the Profile from repository evidence, build the System Map, and list applicable domains as `never`.
- Drop map entries and finding locations that no longer exist. If the map no longer describes the system (rewrite, new platform, new data or permission model), rebuild the map and reset affected Coverage rows to `never` instead of patching.
- Note which checks, scanners, and runtime evidence are actually available in this environment.

### 2. Select a bounded scope

Pick the run's scope in this priority order, and stop adding when the run would no longer be finished credibly in one session:

1. Areas changed since their `Last audited` commit (`git diff --stat <commit>..HEAD`, `git log`), weighted by risk rather than line count.
2. Highest-risk domains never or least-recently covered, including any always-audit surfaces named in the Profile.
3. Open findings to re-verify against current code.

Include at least one end-to-end critical workflow that crosses the selected areas. State the scope and what is explicitly left out before starting. Ask the user only when a choice of priority or risk tolerance would change the scope materially and cannot be inferred.

### 3. Discover

Read [references/coverage.md](references/coverage.md) for the selected domains. For each area:

- Form concrete failure hypotheses, then confirm or falsify them from code, configuration, history, tests, or runtime evidence.
- Trace critical invariants from entry point through domain logic, persistence, and side effects; a locally correct function does not prove the workflow.
- Do not sample only complex-looking files. Include entry points, permission gates, persistence, migrations, background work, integrations, and release paths.
- Finish discovery across the whole scope before repairing anything.
- Record an area with no finding as covered; do not invent findings.

### 4. Classify findings

Every finding needs a trigger (how it is reached), impact, evidence (`file:line`, command output, or reproduction), and a fix direction. Deduplicate symptoms under one root cause. Mark each statement as verified fact or inference; an unconfirmed suspicion is a gap, not a finding.

- `Must Fix`: security, privacy, data loss or corruption, serious incorrectness, unsafe deploy or recovery, or structural damage already blocking reliable development.
- `Should Fix`: real reliability, architecture, test, operational, or maintainability risk worth scheduled work.
- `Needs Decision`: the right outcome depends on product semantics, risk tolerance, or a tradeoff only the user can make.
- `Note`: bounded, acceptable compromise or observation; record the ceiling and what would make it worth revisiting.

Rank by impact, likelihood, blast radius, and reversibility, not by code size or scanner severity. When the same class of issue recurs across cycles, recommend a durable control (test, lint, shared entry point, CI guard) instead of another scan.

### 5. Remediate only when authorized

- Fix only the finding IDs the user authorized. Resolve a blocking `Needs Decision` before choosing a fix direction.
- Make the smallest coherent change and add a regression check at the root-cause boundary.
- Verify each fix yourself: run the relevant checks and re-read the fix diff against the finding's trigger. Mark `fixed` only when closure is visible in current code and supported by that evidence.
- Do not start re-audit rounds. If a fix fails verification or opens a new problem, stop and hand the item to the user as a decision with the evidence.

### 6. Record and report

- Update `AUDIT.md`: System Map changes, each covered domain's commit/date/depth/next focus, and every finding's status and last-verified commit.
- Write `.agent-work/audit/runs/{YYYYMMDD-HHMM}.md` in Chinese by default, keeping paths, symbols, commands, and finding IDs verbatim:

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

- Reply to the user in Chinese by default with the same structure in brief: findings first by severity, then decisions needed, coverage limits, and next focus. Never imply unaudited areas are safe.

A run is complete when every in-scope area has a Coverage update, every finding has evidence, authorized fixes are verified, and the report states its limits.

## Commit trailer

Do not commit unless the user asks. When the user asks to commit a completed audit run, include this trailer exactly once in the commit message so the audit-reminder hook resets its count:

```text
Maintenance-Audit: true
```

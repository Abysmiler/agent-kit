---
name: code-review
description: "Review one bounded change set: a pull request, commit range, uncommitted diff, one implementation section, a repair delta, or a finished multi-section feature, especially AI- or agent-authored changes. Use for requested reviews, merge-readiness checks, and section acceptance. Runs one independent, evidence-backed full review, separates user-owned decisions from agent-fixable defects, and verifies repairs without rescanning stable scope."
---

# Code Review

Review one bounded change set with senior-engineer judgment. Optimize for real merge risk and evidence, not checklist theater, repeated full scans, or style feedback.

## Boundary

- Review exactly the named change set. For a periodic whole-repository audit, use the `code-audit` skill.
- Review only by default. Repair only when the user or orchestrator explicitly authorizes it.
- Treat agent-authored code, summaries, PR descriptions, test claims, and prior review conclusions as plausible but untrusted.
- Preserve user work. Do not reset, clean, merge, approve, push, post comments, or rewrite history unless explicitly asked.
- A subagent that receives a review request is the executor; it must not delegate the same review again.

## Modes

- `FULL`: one bounded change set — a PR, commit range, uncommitted diff, or one section range `base..head` together with its plan/contract. A whole-feature review is `FULL` over `feature_base..feature_head`; focus it on what section reviews cannot prove (cross-section contracts, end-to-end paths, migration/rollout order, requirement coverage, leftover scaffolding) instead of replaying local lines.
- `DELTA`: a repair diff plus its direct impact cone, checked against frozen findings. Never rescans stable scope.

For a section range, also verify: the frozen acceptance criteria, the feature invariants the section touches, that the intermediate repository/runtime state is valid before later sections, and that deferred work is explicit and safe to postpone. Do not report explicitly deferred future-section work as a defect. Section acceptance is provisional; it never means the whole feature is mergeable.

## Depth

Choose one depth; mode and depth are independent.

- `Small`: narrow local behavior, few files, no trust, data, concurrency, migration, release, or public-contract boundary.
- `Medium`: multiple modules or workflows, shared helpers, meaningful UI behavior, API- or persistence-adjacent logic.
- `Large`: refactor, state-model rewrite, migration, auth/permission change, concurrency or background job, destructive operation, architecture transition, broad config/CI change, or an impact cone that is hard to bound.

Any high-risk semantic boundary — security, permissions, persistence/schema, money, time, concurrency, public API — forces `Large`, however small the diff.

Read [references/checklist.md](references/checklist.md) for `Large` depth, and for AI-authored changes or changes to agent tooling, prompts, permissions, or CI.

Flag poor reviewability up front (mixed unrelated goals, unclear intent, giant generated churn, unstable base, missing build environment), then continue with the highest-value evidence available rather than inventing certainty.

## Procedure

1. **Establish reality.** Record mode, exact base and head (or reproducible diff commands), and `git status`. Read repository rules, the plan/contract, and test entry points relevant to the change. Note which checks can actually run here.
2. **Reconstruct intent.** Write a one-sentence intent, explicit non-goals, and the invariants that must stay true, from authoritative repository evidence. Treat claims such as "backward compatible", "test-only", or "all tests pass" as things to verify, not reasons to lower scrutiny.
3. **Map the change and impact cone.** Changed entry points, public APIs, schemas, permissions, state owners, jobs, config, and CI; direct callers and callees; behavior removed; assumptions introduced.
4. **Generate candidates without editing code.** One broad discovery pass, in this lens order: product/domain semantics and end-to-end correctness; data, state, ordering, concurrency, failure atomicity; security, privacy, permissions, trust boundaries; reliability, rollout, rollback, observability, performance; architecture, reuse, unnecessary complexity; tests and CI integrity; AI-agent risks when applicable. For `Medium` and `Large`, trace at least one critical path end to end. Read unchanged context when the diff alone cannot prove behavior. Search for existing implementations before accepting a new abstraction.
5. **Validate and falsify.** For each candidate: state the exact trigger and violated invariant, trace the reachable path, then try to disprove it from code, types, tests, config, or the smallest runnable check. Discard unsupported candidates. Never publish raw hypotheses.
6. **Deduplicate.** Merge symptoms into one root-cause finding with a stable ID (`REV-001`) and all affected instances attached.

## Findings

Every finding states: severity, file/symbol references, trigger, impact, evidence inspected (with remaining uncertainty), and the smallest credible fix direction.

| Severity | Meaning |
|---|---|
| `Must Fix` | Blocks merge: correctness, security, privacy, data loss, permission, migration, or release risk. |
| `Should Fix` | Important before merge unless the user explicitly accepts the risk. |
| `Needs Decision` | User-owned: product semantics, compatibility policy, migration meaning, acceptable risk. Never guess; ask. |
| `Note` | Non-blocking: planned follow-up, bounded debt, or an evidence gap worth recording. |

Do not report: formatting or linter-only issues, preference between equally valid idioms, hypotheticals without a reachable trigger, "add more tests" without naming the missing behavior, performance concerns without plausible scale, or security labels without an asset, path, and impact. Passing tests do not prove correct product semantics, security, or migration safety.

## Repair And Verification

One independent full review per change set. There is no multi-round review loop.

1. **Freeze** finding IDs, wording, evidence, and acceptance criteria before any repair. A fixer never redefines a finding while fixing it.
2. **Stop first** when a `Needs Decision` item prevents a safe fix; ask only the decisions required to proceed.
3. **Repair** (only when authorized): the smallest coherent change for the frozen agent-fixable findings. No unrelated cleanup.
4. **Self-verify** (main/orchestrating agent): run the relevant checks and re-read the repair diff against each frozen finding. Close a finding only on code-visible evidence plus a passing check — never on the fixer's explanation alone.
5. **Independent `DELTA` review** only when the repair itself touched a high-risk semantic boundary (listed under Depth) or the user asks. Use a fresh reviewer.
6. **Still unresolved?** If any `Must Fix` or `Should Fix` remains open after step 4 (or step 5 when it ran), stop and hand the decision to the user: authorize more repair, split the change, accept the risk, or block. Do not start another round on your own.

A `DELTA` reviewer checks only: hunks changed by the repair; callers, contracts, schemas, permissions, and tests the repair invalidated; and whether each frozen finding is actually closed. It returns `reset-required` instead of a verdict when the repair rewrote a substantial part of the original change, expanded scope, or the base/head moved outside the repair — the user then decides whether to run a new `FULL` review.

## Reviewer Independence

- Run the review in a fresh `[tier: review]` context, separate from the author and the fixer.
- Give the `FULL` reviewer only the scope, the plan/contract, and this skill. Do not leak suspected issues, prior conclusions, or repair narratives.
- Give the `DELTA` reviewer the repair range, the frozen finding IDs, and one-line titles of already-closed root causes — nothing else from earlier reasoning.

## Verdict

- `FULL`: `mergeable` | `not-mergeable` | `insufficient-evidence`. For a section range: `accepted` | `blocked` | `insufficient-evidence`.
- `DELTA`: `delta-verified` | `delta-blocked` | `reset-required`.

A positive verdict requires all of: no open `Must Fix`; no `Should Fix` the user has not accepted; no blocking `Needs Decision`; required deterministic checks pass, or their blockers and residual risk are stated. One clean review is sufficient — never require a second empty pass.

## Report

Write the user-facing report in Chinese by default. Keep code symbols, paths, commands, error text, and finding IDs verbatim. Lead with findings ordered by severity; if none are actionable, say so directly and state residual risk. Distinguish verified facts from inferences and unverified claims. Never claim a finding is resolved unless current code and verification evidence support closure.

Write a report file only when an orchestrator asks for one or the review must survive context compaction: `.agent-work/reviews/{id}-r{N}.md` (`{id}` is the section ID or a short change slug). Keep no other ledgers. Template:

```markdown
# Review {id} r{N}

- Mode / depth: FULL | DELTA / Small | Medium | Large
- Range: {base}..{head} (or diff command); worktree state
- Verdict: ...
- Intent and invariants: ...

## Findings

### REV-001 — {root-cause title}
- Severity: Must Fix | Should Fix | Needs Decision | Note
- Where: {file:line, symbol, route}
- Trigger: ...
- Impact: ...
- Evidence: ... (uncertainty: ...)
- Fix direction: ...
- Status: open | fixed-verified | accepted-risk | deferred

## Coverage

- Lenses and critical paths reviewed: ...
- Checks run / not run (with reason): ...
- Residual risk and assumptions: ...
```

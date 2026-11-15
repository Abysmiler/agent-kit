# Integration and Convergence Guide

Use this guide to distinguish section acceptance from feature readiness and to interpret the single-clean-review / three-round hard-cap policy.

## Contents

1. [Review roles](#1-review-roles)
2. [Single-clean section acceptance](#2-single-clean-section-acceptance)
3. [Three-round hard cap](#3-three-round-hard-cap)
4. [Hard-cap user decision](#4-hard-cap-user-decision)
5. [Integration checkpoints](#5-integration-checkpoints)
6. [Final integration review](#6-final-integration-review)
7. [Reset and evidence invalidation](#7-reset-and-evidence-invalidation)
8. [Human decision points](#8-human-decision-points)
9. [Final readiness gate](#9-final-readiness-gate)

## 1. Review roles

### SECTION

The round-1 full review of one frozen section range plus its direct impact cone, from a fresh reviewer context. Later counting rounds are `DELTA` reviews (below).

Possible local result:

- material actionable findings;
- no new material actionable finding;
- blocked by a genuine decision/evidence gap.

The parent workflow, not the individual reviewer, decides whether a counting round is clean.

### DELTA counting rounds

After a repair, the counting round is a `DELTA` review of the repair delta plus its invalidated impact cone. A `delta-verified` result (all frozen findings closed, no new blocking defect in the cone) is a clean counting round and accepts the section. A full `SECTION` review runs again only after a reset trigger, so stable scope is never rescanned.

### INTEGRATION

A cross-section review of the assembled feature after accepted active leaf sections compose on the actual feature head. It focuses on emergent behavior rather than replaying every section line.

## 2. Single-clean section acceptance

A section is provisionally accepted only when all are true:

- section contract and base/head are stable and recorded;
- required checks pass or an external evidence blocker is explicit;
- no unresolved `Must Fix`, unaccepted `Should Fix`, or blocking `Needs Decision` remains;
- deferred work has an explicit later owner and does not make the current intermediate state invalid;
- one counting round is clean: a coverage-complete full `SECTION` review (round 1) with no new material actionable root cause, or a `delta-verified` round after repair.

The counting reviewer must not be primed with “the previous round was clean”, prior persuasive conclusions, or repair narratives. Frozen finding IDs and closed root-cause IDs (IDs and one-line titles only) are shared to prevent re-raising closed items.

## 3. Three-round hard cap

Per active section attempt:

- Maximum counting rounds: **3** (full round 1, `DELTA` rounds after repair).
- Soft cap: **none**.
- Acceptance condition: a clean counting round within those three.
- Round 4 on the same attempt is forbidden without an explicit recorded user `continue` decision.

Examples:

```text
R1 clean
=> accepted in 1 round
```

```text
R1 findings -> repair
R2 delta-verified
=> accepted in 2 rounds
```

```text
R1 findings -> repair
R2 delta findings -> repair
R3 delta findings -> repair
=> not accepted; hard-cap user decision
```

## 4. Hard-cap user decision

Three non-convergent counting rounds are treated as evidence about the decomposition — but the response is a user decision, not an autonomous rewrite. Common evidence patterns:

- multiple independent behaviors were placed in one section;
- one section spans several state/ownership boundaries;
- repairs repeatedly disturb adjacent contracts;
- the test oracle is too broad or indirect;
- expand/migrate/contract phases were collapsed together;
- an enabling refactor and feature behavior are entangled;
- hidden cross-section dependencies were left inside the section.

The decision therefore:

1. preserves the failed code state on `agent-kit/backup/***`;
2. summarizes all counting rounds with their root-cause patterns;
3. asks the user to choose, in order: `continue` (up to two more counting rounds), `split`, `accept-risk`, or `block`;
4. on `split`, asks a `[tier: plan]` subagent to re-decompose only that section, validates the new descendant plan, and restarts implementation from the failed parent's original `section_base` — salvaging failed-attempt commits only if the decision explicitly authorizes it;
5. on `accept-risk`, records every remaining finding as explicit debt/decisions and marks the section accepted with debt.

Never autonomously discard near-converged work or start re-implementation at the hard cap; the user owns that trade-off.

## 5. Integration checkpoints

Use a checkpoint when later sections begin consuming a newly established cross-section contract, including:

- API producer + first real consumer;
- schema expansion + read/write migration;
- permission policy + enforcement path;
- producer + queue/worker + retry behavior;
- new state owner + downstream consumers;
- feature flag + old/new path parity;
- independently developed branches after combination.

Checkpoint evidence should include combined head, included sections, contracts under test, happy/negative/partial-failure paths, commands/results, rollback/disable path, and known not-yet-included sections.

Checkpoint outcomes:

- `checkpoint-passed`;
- `checkpoint-blocked`;
- `checkpoint-insufficient-evidence`.

A checkpoint can invalidate prior local evidence when actual composition disproves a section assumption. Preserve the original review/replan lineage rather than rewriting history.

## 6. Final integration review

After all active leaf sections are accepted, close the feature. Run the final `INTEGRATION` review only when at least one applies: the feature crossed a high-risk semantic boundary; more than three active leaf sections were accepted; a hard-cap split occurred; or the user/governing instructions request it. Otherwise the deterministic full-feature validation suite plus the last section's review evidence closes the feature.

When the review runs, assess the assembled feature against the original contract and do not replay accepted local line.

### Original intent

- Does behavior satisfy the original user/operator outcome?
- Are non-goals still respected?
- Is every requirement mapped to implementation and evidence?

### Cross-section contracts

- API request/response and error semantics;
- schema/data ownership and migration order;
- state ownership and synchronization;
- authorization/tenancy consistency;
- event ordering, retry, idempotency, cancellation;
- shared UI state and loading/error/empty states;
- cleanup and feature-flag lifecycle.

### End-to-end and operations

- representative happy path;
- negative permission/input path;
- partial-failure/retry path;
- rollback/disable behavior;
- logs/metrics/traces/audit signals;
- performance/resource bounds where relevant;
- security/privacy/secret handling;
- documentation/config/runbook completeness.

### Branch integrity

- only feature-related changes are present;
- generated artifacts are reproducible;
- tests were not weakened to force green;
- temporary scaffolding is removed or explicitly owned;
- active descendant heads and review evidence correspond to the actual feature head.

## 7. Reset and evidence invalidation

A section review attempt should be treated as a new baseline when a material change alters:

- section goal or acceptance criteria;
- public API/serialized contract;
- schema/data ownership/migration order;
- auth/authorization/tenancy/privacy semantics;
- concurrency/order/retry/idempotency/destructive behavior;
- architecture/state owner/dependency direction;
- rollout/rollback/feature-flag semantics;
- scope beyond the frozen contract;
- base/head outside tracked implementation/repair operations.

Hard-cap re-decomposition is stronger than an ordinary reset: the parent attempt is retired and descendants start from the parent's original base.

## 8. Human decision points

Require the user/accountable owner for:

- ambiguous business/product behavior;
- compatibility policy choices;
- migration/backfill meaning;
- acceptable data/security/operational risk;
- rollout cohort/timing policy when not already specified;
- conflicting authoritative requirements;
- the three-round review hard cap (continue / split / accept-risk / block).

Do not require user approval again, after a recorded `split` choice, merely to:

- create the hard-cap backup branch;
- invoke the `[tier: plan]` decomposer;
- create the retry branch/worktree;
- extract the first descendant and resume implementation.

Those follow the recorded decision under the already delegated execution authority. At lineage depth `3`, a further split should recommend re-planning the feature boundary instead of depth-`4+` recursion.

## 9. Final readiness gate

State `mergeable` only when:

- all active leaf sections are provisionally accepted;
- parent sections retired by hard-cap splits have complete lineage/evidence;
- all full-feature requirements are covered;
- required integration checkpoints pass;
- the required final gate — an `INTEGRATION` review when triggered, otherwise the deterministic full-feature validation suite plus the last section's review evidence — has no unresolved material merge blocker;
- full-feature deterministic checks pass or explicit external blockers/residual risk are reported;
- rollout, rollback, migration, observability, and cleanup obligations are resolved or explicitly accepted.

Otherwise use `not-mergeable` or `insufficient-evidence`.

---
name: sectioned-feature-development
description: "Plan and execute non-trivial software changes as reviewable sections with durable feature state, per-section contracts, independent implementation/review agents, single-clean-review section acceptance, delta-scoped post-repair re-review, a three-round hard cap escalated to a user decision, integration checkpoints, and a conditional final cross-section gate. Use when any trigger applies: the change crosses a high-risk semantic boundary; architecture or state ownership changes; the impact cone is difficult to bound; a previous whole-change implementation/review failed to converge; or expected behavioral edits exceed roughly 800 lines across more than three modules, packages, services, pages, or workflows."
---

# Sectioned Feature Development

Develop one large feature as a sequence of bounded sections. Each section must be independently implementable, testable, reviewable, and reversible enough to diagnose. Review round 1 is one fresh, coverage-complete full `SECTION` review; after a repair, the next counting round is a `DELTA` review of the repair delta plus its impact cone, so stable scope is never rescanned. A section is provisionally accepted when a counting round finds no new material actionable issue: a clean full review, or a `delta-verified` round after repair. If three counting rounds fail to reach that condition, preserve the failed attempt and stop at a user decision with bounded options — authorize more rounds, split the section through `[tier: plan]` re-decomposition, accept the residual risk, or block for human intervention.

## Boundary and authority

- Follow repository-local instructions before this skill.
- Use this skill for one feature, refactor, migration, or architectural transition, not for periodic repository audits.
- Determine execution authority before changing product code:
  - `PLAN_ONLY`: write/validate planning artifacts only.
  - `EXECUTE_NO_COMMIT`: implement and validate without branch/commit operations.
  - `EXECUTE_WITH_COMMITS`: create/switch bounded feature or retry branches/worktrees and make section implementation/repair commits.
- A planning or review request alone does not authorize commits.
- If governing Custom Instructions explicitly delegate branch/commit authority to the `sectioned-feature-development` skill, that scoped delegation takes precedence over their general no-commit rule only for this workflow's bounded feature/retry branches and implementation/repair/snapshot commits.
- Never push, merge, create a pull request, rewrite published history, clean, delete user work, or discard unrelated changes unless separately authorized.
- The three-round review hard cap **is** a user-decision point. When it fires, preserve the failed attempt, present the bounded options, and act only on the recorded user choice; do not autonomously discard work or start re-implementation.
- Count recursive split depth from the original section: `S03` is depth `0`, `S03.1` is depth `1`, `S03.1.1` is depth `2`, and `S03.1.1.1` is depth `3`. Report the depth in the hard-cap decision; when a split would create depth `4` or deeper, recommend re-planning the feature boundary instead of deeper recursion.
- Still stop when a real user-owned decision is required: product semantics, compatibility policy, migration meaning, acceptable risk, rollout behavior, or another non-inferable business choice.

## Trigger

Use this workflow when any condition holds:

- The change crosses persistence, schema, money, time, units, security, permissions, tenancy, routing, concurrency, background jobs, public API, deployment, or shared-state boundaries.
- Architecture or state ownership changes.
- The impact cone is difficult to bound.
- A previous whole-change implementation or review loop failed to converge.
- Expected behavioral edits exceed roughly 800 lines **and** span more than three modules, packages, services, pages, or workflows.

Size alone (line count or module count) never triggers this workflow; semantic risk and reviewability dominate raw line count. Ordinary-size changes use the normal plan/implement/review path with a single review.

## Required artifacts

Use these paths unless repository rules define equivalent ones:

```text
.agent-work/
├── PLAN-FULL.md
├── PLAN.md
├── FEATURE-STATE.md
├── sections/
│   ├── S01-CONTRACT.md
│   ├── S01-HANDOFF.md
│   └── ...
├── reviews/
│   ├── S01-SECTION-r01.md
│   ├── S01-SECTION-r02.md
│   └── ...
├── replans/
│   ├── S01-g01-HARD-CAP.md
│   └── ...
└── plans/
    └── {YYYYMMDD-HHMM}_FULL.md
```

Keep `PLAN-FULL.md` and `FEATURE-STATE.md` authoritative. Chat history is not durable project state.

## Load references progressively

- Read [references/section-planning.md](references/section-planning.md) before dividing or re-dividing a feature.
- Read [references/orchestration-protocol.md](references/orchestration-protocol.md) before delegating implementation, review, repair, or hard-cap recovery.
- Read [references/integration-and-convergence.md](references/integration-and-convergence.md) before accepting a section or running integration gates.
- Read [references/artifact-schemas.md](references/artifact-schemas.md) when creating, extracting, validating, carrying forward, or archiving artifacts.

## State machine

```text
PREFLIGHT
  -> FEATURE_CONTRACT
  -> SECTION_PLAN
  -> PLAN_GATE
  -> SECTION_CONTRACT
  -> IMPLEMENT
  -> LOCAL_VALIDATE
  -> COMMIT_IF_AUTHORIZED
  -> REVIEW_ROUND (full on round 1 or after reset; DELTA after repair)
       -> CLEAN -> SECTION_ACCEPTED
       -> FINDINGS -> REPAIR -> COMMIT -> REVIEW_ROUND
       -> RESET_TRIGGER -> FULL_SECTION_REVIEW
       -> USER_DECISION -> BLOCK
       -> ROUND_3_WITHOUT_CLEAN -> HARD_CAP_DECISION
  -> SECTION_ACCEPTED
  -> INTEGRATION_CHECKPOINT when triggered
  -> next SECTION_CONTRACT
  -> CONDITIONAL_FINAL_INTEGRATION_REVIEW
  -> FINAL_VALIDATE
  -> ARCHIVE_AND_REPORT

HARD_CAP_DECISION (user)
  -> CONTINUE -> REVIEW_ROUND (up to two more counting rounds)
  -> SPLIT -> HARD_CAP_REPLAN (backup -> [tier: plan] split -> retry from original section base)
  -> ACCEPT_RISK -> SECTION_ACCEPTED_WITH_DEBT
  -> BLOCK
```

Do not advance because an agent says it is done. Advance only when the corresponding artifact and evidence gate is satisfied.

## Phase 0: Preflight and feature contract

1. Inspect repository rules, architecture sources, current branch, `git status`, relevant recent commits, build/test entry points, and validation environment.
2. Freeze the exact `feature_base` commit.
3. Use the repository's code graph/index first when governing instructions require it.
4. Create `.agent-work/PLAN-FULL.md` and record:
   - one-sentence outcome;
   - observable behavior;
   - explicit non-goals;
   - feature-level invariants;
   - authoritative constraints;
   - full acceptance criteria and validation commands;
   - ownership/state boundaries;
   - compatibility, migration, rollout, rollback, flag, observability, and cleanup requirements.
5. Identify the smallest enabling refactor if direct work would materially worsen an unsafe ownership boundary or under-tested core path.
6. In `EXECUTE_WITH_COMMITS`, create the feature branch before product-code implementation.

## Phase 1: Divide the feature

Create all initial sections in `PLAN-FULL.md` before implementation.

Prefer:

1. walking skeleton / contract proof when integration is uncertain;
2. vertical behavior slices;
3. explicit expand-migrate-contract or branch-by-abstraction stages when compatibility requires them;
4. cleanup/contraction only after consumers have moved and evidence proves the old path is unused.

Every section needs:

- stable ID such as `S01`;
- goal and observable behavior increment;
- dependency/predecessor relationship;
- expected files/symbols/workflows and semantic boundaries;
- non-goals and named deferred work;
- touched feature invariants;
- falsifiable acceptance criteria;
- exact validation commands/evidence;
- compatibility/rollout/recovery implications;
- estimated size/risk and split trigger.

A valid section can be understood by one reviewer without loading the entire feature implementation and can be verified without undocumented future work.

Use the helper when practical:

```bash
python {skill-dir}/scripts/section_plan.py validate .agent-work/PLAN-FULL.md
python {skill-dir}/scripts/section_plan.py list .agent-work/PLAN-FULL.md
python {skill-dir}/scripts/section_plan.py extract \
  .agent-work/PLAN-FULL.md S01 --output .agent-work/PLAN.md
```

Hierarchical descendant IDs are valid after a hard-cap split, for example `S03 -> S03.1, S03.2` and later `S03.1 -> S03.1.1, S03.1.2`.

## Phase 2: Plan gate

Before implementation, verify:

- every full-feature requirement maps to section evidence and final integration evidence;
- dependencies are explicit and acyclic;
- high-risk boundaries have one authoritative owner and an oracle;
- cross-section contracts/checkpoints are named;
- refactor and behavior are separated unless inseparable;
- no section is a vague “finish/integrate everything” bucket;
- each section is small enough to plausibly converge under the three-round review budget.

Use one clean plan reviewer for ambiguous/high-risk plans. It challenges decomposition and contracts; it does not implement.

## Phase 3: Freeze one current section

For the next dependency-ready section:

1. Record `section_base` as the exact accepted predecessor head.
2. Extract exactly that section into `.agent-work/PLAN.md`.
3. Create `.agent-work/sections/{ID}-CONTRACT.md`.
4. Resolve genuine open business decisions before code.
5. Set `replan_generation` to `0` for an original section, or inherit/increment lineage for descendants.
6. Update `FEATURE-STATE.md` with section ID, lineage, base, execution path, expected checks, and review round `0`.

Ordinary implementation must not silently redefine the frozen section contract.

## Phase 4: Implement and locally validate

Delegate exactly one current section.

Default routing by role tier (map to the host's available sub-agent tiers; see
the Model Routing Tiers section of the core instructions):

- ordinary implementation: a `[tier: execute]` subagent;
- high-risk implementation or repair: a `[tier: review]` subagent;
- section review: a fresh `[tier: review]` subagent (reviewer context);
- hard-cap section re-decomposition: a `[tier: plan]` subagent.

The implementer receives repository rules, feature goal/invariants, current `PLAN.md`, section contract, exact `section_base`, and required checks. It must not implement future sections.

Require:

- smallest code change satisfying the section contract;
- meaningful behavior/edge/error regression coverage;
- targeted checks before broad checks;
- `.agent-work/sections/{ID}-HANDOFF.md` with files, decisions, commands/results, limitations, and head.

In `EXECUTE_WITH_COMMITS`, commit the coherent section implementation before review.

## Phase 5: Section review loop

Review round 1 is one fresh, independent, coverage-complete `code-review` skill invocation in `SECTION` mode over the current `section_base..section_head` plus the direct semantic impact cone. Every later counting round is a fresh `DELTA` review of the previous repair delta plus its invalidated impact cone, so stable scope is never rescanned. A reset trigger restores a full `SECTION` review.

Use a clean `[tier: review]` reviewer subagent for every counting round. Do not preload prior reviewer reasoning, repair narratives, or whether previous rounds were clean. Do share the frozen finding IDs of the current round and the cumulative list of already-closed root-cause IDs (IDs and one-line titles only) so the reviewer does not re-raise closed items.

Round 1 packet:

```text
Review mode: SECTION
Section: {ID}
Range: {section_base}..{section_head}
Feature contract: .agent-work/PLAN-FULL.md
Section contract: .agent-work/sections/{ID}-CONTRACT.md
Implementation handoff: .agent-work/sections/{ID}-HANDOFF.md
Output: .agent-work/reviews/{ID}-SECTION-r{NN}.md
Use: the code-review skill
```

Post-repair packet:

```text
Review mode: DELTA
Section: {ID}
Repair range: {repair_base}..{section_head}
Frozen findings from round {NN}: {IDs}
Closed root causes (IDs and one-line titles only): {list}
Feature contract: .agent-work/PLAN-FULL.md
Section contract: .agent-work/sections/{ID}-CONTRACT.md
Output: .agent-work/reviews/{ID}-SECTION-r{NN}.md
Use: the code-review skill
```

Maintain `review_round = 0` in `FEATURE-STATE.md`.

For at most three counting rounds:

1. Increment `review_round` and run the round: full `SECTION` for round 1 or after a reset trigger, `DELTA` otherwise.
2. Main agent inspects the report and current repository state.
3. If a finding requires a genuine user-owned decision, record it and block immediately.
4. If there is **no new material actionable finding** — a coverage-complete clean full review, or a `delta-verified` DELTA round — mark the section `section-accepted`.
5. If there is any new `Must Fix`, `Should Fix`, or blocking `Needs Decision` finding:
   - deduplicate symptoms under stable root-cause IDs;
   - send only agent-fixable findings from that round to a `[tier: review]` repair agent;
   - run the relevant deterministic checks;
   - in `EXECUTE_WITH_COMMITS`, commit the repair;
   - update the handoff and `section_head`;
   - run the next counting round as a `DELTA` review of this repair delta plus its impact cone, or a full `SECTION` review when a reset trigger fires.

The following do not count as material unless they imply a material defect in the frozen section: repeated wording of an already-closed root cause, explicitly deferred future-section work, unsupported hypotheses, style preference, `Should Plan`, or bounded debt.

A repair wave may still use targeted internal checks for risky fixes; they do not advance `review_round` — the counting round after repair is itself the `DELTA` review.

### Three-round hard cap

After counting round 3, if the section has not been accepted, do **not** start round 4. Enter `HARD_CAP_DECISION`: preserve the failed attempt (Phase 6.1), then stop and ask the user to choose one recorded option:

- `continue`: authorize up to two more counting rounds for the same attempt;
- `split`: run the re-decomposition protocol (Phase 6.3 onward);
- `accept-risk`: accept the current implementation with remaining findings recorded as explicit debt/decisions (`SECTION_ACCEPTED_WITH_DEBT`);
- `block`: stop for human intervention on the root cause.

Present the options in that order with the round-by-round evidence. At lineage depth `3`, recommend re-planning the feature boundary over a depth-`4+` split. Cherry-picking failed-attempt commits into a retry requires explicit authorization in the same decision.

## Phase 6: Hard-cap preservation and user decision

Treat three-round non-convergence as evidence that the current section boundary may be too broad, too coupled, or insufficiently isolated for reliable agent implementation/review. Preserve the failed attempt, then stop at the hard-cap user decision (Phase 5). Only a recorded `split` choice enters the re-decomposition path below.

### 6.1 Preserve the failed attempt

1. Record `failed_tip = HEAD`, `section_base`, current section ID, replan generation, all counting-round review files, repair commits, and check results.
2. Ensure current-section-owned code changes are committed when commits are authorized. Never absorb unrelated user changes into the snapshot.
3. Create a backup branch **without prompting for authorization**:

```text
agent-kit/backup/{feature-slug}-{section-id}-g{generation}-{YYYYMMDD-HHMMSS}
```

Point it at `failed_tip`. Prefer creating the ref without switching branches.
4. Write `.agent-work/replans/{section-id}-g{generation}-HARD-CAP.md` using the bundled template. Summarize, round by round, what each counting round found, which root causes were repaired, what recurred, and why the section did not converge. Record the user decision, the options as presented, and any authorization it granted (extra rounds, salvage/cherry-pick, risk acceptance).

The backup is evidence and a recovery point. Do not continue implementing on that failed code state unless the user decision explicitly authorizes it (`continue` or `accept-risk`).

### 6.2 Present the hard-cap user decision

Stop and ask the user to choose, in this order: `continue` (up to two more counting rounds), `split` (re-decomposition per Phase 6.3), `accept-risk` (record remaining findings as explicit debt/decisions and mark `SECTION_ACCEPTED_WITH_DEBT`), or `block` (human intervention on the root cause). Attach the round-by-round evidence and the current lineage depth; at depth `3`, recommend re-planning the feature boundary over a depth-`4+` split. Record the choice in `FEATURE-STATE.md` and the hard-cap summary.

On `continue`, resume Phase 5 counting rounds against the same attempt. On `accept-risk`, populate the deferred-work/residual-risk ledger with every remaining finding. On `block`, stop.

### 6.3 Escalate decomposition to a `[tier: plan]` subagent (split choice only)

Entered only after the user records a `split` choice. Before spawning the `[tier: plan]` decomposer, calculate the depth of the descendants the split would create; at depth `4+`, recommend re-planning the affected parent/feature boundary instead of splitting.

Spawn a clean `[tier: plan]` subagent. Explicitly tell it:

- the currently failing section ID/title and its `section_base`;
- the feature goal, invariants, and current `PLAN-FULL.md`;
- the backup branch and failed tip;
- all counting-round review files plus a concise round-by-round issue summary;
- that the hard cap was reached and the user chose to split;
- that it must **split only the current section in `PLAN-FULL.md` into smaller independently implementable/reviewable descendant sections**;
- that accepted predecessor sections and user-owned feature semantics are frozen;
- that it must update requirement coverage, dependency edges, downstream `Requires`, checkpoints, and deferred-work ownership affected by the split;
- that it must not implement product code;
- that descendants should use hierarchical lineage IDs such as `S03.1`, `S03.2`; if a descendant later fails, continue the hierarchy;
- the current lineage depth; depth-`4+` descendants require a recorded user re-plan choice.

The `[tier: plan]` replan must use the review-round histories as decomposition evidence: repeated bug classes should become explicit boundaries, invariants, oracles, or separate descendant sections rather than being copied as prose into one smaller-looking but semantically identical section.

### 6.4 Main-agent plan rewrite and validation

After the `[tier: plan]` subagent returns:

1. Main agent inspects and, if necessary, normalizes the `PLAN-FULL.md` split. The `[tier: plan]` subagent proposes the decomposition; the main agent owns final artifact integrity.
2. Preserve the parent section as historical lineage with state `SPLIT_AFTER_HARD_CAP`; do not schedule it again.
3. Validate the revised `PLAN-FULL.md` with `section_plan.py` and verify the dependency graph remains acyclic and every full-feature requirement remains covered.
4. If the proposed split requires a new user-owned product decision, block only for that decision. When descendants would be depth `4+`, recommend re-planning the feature boundary in the decision instead of splitting deeper.
5. Update `FEATURE-STATE.md` with backup branch, failed tip, hard-cap summary and user decision, descendant IDs, and next ready descendant.

### 6.5 Retry from the original section base

Do **not** cherry-pick the failed section implementation or repair commits into the retry unless the user's hard-cap decision explicitly authorized salvaging verified parts.

Start the descendant sequence from the failed parent section's original `section_base`:

- In `EXECUTE_WITH_COMMITS`, create a new retry branch/worktree from `section_base`. Prefer a new branch/worktree rather than resetting the failed branch.
- Carry forward only orchestration artifacts required for the revised plan/state; do not carry failed product-code diffs.
- If unrelated user changes make branch switching unsafe, leave the failed worktree untouched and create an isolated retry worktree from `section_base`.
- Create retry worktrees under the repository-root `.worktrees/` workspace and register the retry task in `.worktrees/current-agents/` per the manual-git-worktrees skill.
- Record the new retry path/branch in `FEATURE-STATE.md`.

Then the **main agent** extracts the first dependency-ready descendant from revised `PLAN-FULL.md` into `.agent-work/PLAN.md` and resumes Phase 3 → Phase 5 with the normal implementer/reviewer agents.

Hard-cap splitting recurs only through repeated user `split` decisions. If a descendant such as `S03.1` itself reaches the three-round hard cap, preserve that failed attempt and present the decision again; at lineage depth `3`, recommend re-planning the feature boundary over a depth-`4+` split.

## Phase 7: Integration checkpoints

Run a targeted checkpoint when a public contract, schema, permission model, state owner, queue, deployment path, feature flag, or dependency cluster becomes consumable by later sections.

Verify cross-section contracts and representative end-to-end paths without reopening every accepted local line. A checkpoint may invalidate an accepted section only when actual combined behavior disproves its frozen contract evidence.

Parallelize only sections with accepted dependencies, distinct semantic owners/contracts, isolated worktrees, and deterministic integration order. Parallel worktrees must follow the `.worktrees/current-agents/` registry conflict-check protocol (see the manual-git-worktrees skill).

## Phase 8: Final feature gate

After all active leaf sections are accepted and all deferred items are resolved or explicitly approved, close the feature.

Run a final `code-review` skill `INTEGRATION` review over `feature_base..feature_head` only when at least one applies:

- the feature crossed a high-risk semantic boundary;
- more than three active leaf sections were accepted;
- a hard-cap split occurred;
- the user or governing instructions explicitly request it.

Otherwise skip the `INTEGRATION` review: run the deterministic full-feature validation suite and state readiness from that evidence plus the last accepted section's review. Do not run a late integration checkpoint and the final review over the same composition scope; the final review subsumes the checkpoint.

When it runs, focus on what section reviews cannot prove alone:

- original full-feature behavior and non-goals;
- cross-section API/schema/state/permission/ordering/error contracts;
- end-to-end critical paths and combined edge cases;
- migration, compatibility, rollout, rollback, flags, cleanup;
- observability, performance, security, privacy, operational readiness, documentation;
- requirement coverage and branch-scope integrity.

Repair integration findings in bounded scope and rerun the necessary integration evidence. Do not mechanically replay all accepted section reviews.

Then run the deterministic full-feature validation suite and state final readiness as `mergeable`, `not-mergeable`, or `insufficient-evidence`.

## Phase 9: Archive and report

1. Update `FEATURE-STATE.md` with every active/retired section lineage, base/head, verdict, review rounds, backup branch, hard-cap decision/replan, checks, decisions, and residual risk.
2. Delete transient `.agent-work/PLAN.md` only after its section is accepted, split, or explicitly abandoned and durable artifacts exist.
3. Move `.agent-work/PLAN-FULL.md` to `.agent-work/plans/{YYYYMMDD-HHMM}_FULL.md` after final reporting.
4. Keep contracts, handoffs, review evidence, and hard-cap summaries unless repository policy says otherwise.
5. Report in Chinese by default: feature result, section lineage/status, hard-cap splits, findings repaired, checks, decisions, integration result, residual risk, and maintainability judgment.

## Non-negotiable rules

- One implementer works on one extracted section/descendant at a time.
- Review round 1 is a fresh full `SECTION` review from a clean reviewer context; every later counting round is a fresh `DELTA` review of the repair delta plus its impact cone unless a reset trigger fires.
- Section acceptance requires one clean counting round: a coverage-complete full review, or a `delta-verified` round after repair.
- Reviewer independence means no preloaded reasoning; frozen finding IDs and closed root-cause IDs (IDs and titles only) are shared to prevent re-raising closed items.
- Three counting rounds is the hard cap; any round beyond it requires an explicit recorded user `continue` decision.
- At the hard cap, preserve the failed tip and present the bounded options (continue / split / accept-risk / block); never discard or reimplement autonomously.
- A `split` choice invokes a `[tier: plan]` subagent; a depth-`4+` split should recommend re-planning the feature boundary.
- Reimplementation after a split starts from the failed parent section's original base, not from its repeatedly repaired code, unless the user decision explicitly authorizes salvaging verified parts.
- Failed-attempt commits are preserved on `agent-kit/backup/***` and are not cherry-picked by default.
- A repair agent does not declare its own work accepted.
- New user-owned semantics require a real decision; ordinary technical decomposition does not.
- Section acceptance is provisional; the conditional final gate (integration review or full validation suite) still applies.

# Orchestration Protocol

Use this reference when the main agent delegates planning, section implementation, section review, repair, hard-cap decisions, and final integration to separate agent contexts.

## Contents

1. [Roles](#1-roles)
2. [Context packets](#2-context-packets)
3. [Profile routing](#3-profile-routing)
4. [Section orchestration algorithm](#4-section-orchestration-algorithm)
5. [Three-round hard cap and user decision](#5-three-round-hard-cap-and-user-decision)
6. [Commit and branch discipline](#6-commit-and-branch-discipline)
7. [Worktrees and retry isolation](#7-worktrees-and-retry-isolation)
8. [Decision handling](#8-decision-handling)
9. [State integrity](#9-state-integrity)

## 1. Roles

### Main orchestrator

Owns the feature contract, `PLAN-FULL.md`, dependency graph, execution state, subagent prompts, review-round accounting, backup/retry branch selection, and final acceptance gates. It must inspect repository state rather than trusting agent prose.

### Plan reviewer

Challenges initial section boundaries, dependencies, ownership, invariants, test oracles, compatibility, rollout, rollback, and integration checkpoints. It does not implement.

### Section implementer

Receives one extracted section and frozen contract. It implements only that section, runs requested checks, and records handoff evidence.

### Section reviewer

A fresh `[tier: review]` context running the `code-review` skill. Round 1 is a full `SECTION` review of the section range and direct semantic impact cone; later counting rounds are `DELTA` reviews of the repair delta plus its invalidated cone. It receives frozen finding IDs and closed root-cause IDs (IDs and one-line titles only), not prior reviewer reasoning or repair narratives.

### Repair agent

A `[tier: review]` context receiving the current round's frozen agent-fixable findings. It makes the smallest coherent repair, runs relevant checks, and records what changed. It does not decide whether the section is accepted.

### Hard-cap decomposer

A clean `[tier: plan]` subagent invoked only after the user records a `split` choice at the three-round hard cap. It receives the failed section, original section base, current `PLAN-FULL.md`, and the review-round histories. It splits only that section into smaller descendants and updates affected plan edges; it does not implement product code.

### Integration reviewer

A clean reviewer focused on cross-section composition and full-feature acceptance after active leaf sections are accepted.

### Decision owner

The user or accountable maintainer. Only genuine product semantics, compatibility policy, migration meaning, acceptable risk, rollout behavior, or other non-inferable business choices require this authority.

## 2. Context packets

Keep packets explicit. Do not preload persuasive history where independence matters.

### Implementer packet

```text
Working path: {path}
Feature plan: .agent-work/PLAN-FULL.md
Current execution plan: .agent-work/PLAN.md
Section: {ID}
Section contract: .agent-work/sections/{ID}-CONTRACT.md
Section base: {section_base}
Feature invariants: {IDs}
Required checks: {commands}
Commit authority: {mode}
Do not implement future sections.
```

### Review packets

Round 1 (full `SECTION`):

```text
Review mode: SECTION
Working path: {path}
Section: {ID}
Range: {section_base}..{section_head}
Feature contract: .agent-work/PLAN-FULL.md
Section contract: .agent-work/sections/{ID}-CONTRACT.md
Implementation handoff: .agent-work/sections/{ID}-HANDOFF.md
Output: .agent-work/reviews/{ID}-SECTION-r{NN}.md
Use: the code-review skill
```

Post-repair counting round (`DELTA`):

```text
Review mode: DELTA
Working path: {path}
Section: {ID}
Repair range: {repair_base}..{section_head}
Frozen findings from round {NN}: {IDs}
Closed root causes (IDs and one-line titles only): {list}
Feature contract: .agent-work/PLAN-FULL.md
Section contract: .agent-work/sections/{ID}-CONTRACT.md
Output: .agent-work/reviews/{ID}-SECTION-r{NN}.md
Use: the code-review skill
```

Do not include prior reviewer reasoning, repair narratives, or whether the last round was clean. Sharing closed root-cause IDs (IDs and titles only) is required, not a violation of independence — it prevents re-raising closed items. The main orchestrator, not the reviewer, owns the acceptance rule.

### Repair packet

```text
Working path: {path}
Section: {ID}
Current reviewed head: {head}
Authorized findings from round {NN}: {IDs}
Review file: .agent-work/reviews/{ID}-SECTION-r{NN}.md
Frozen acceptance criteria: {criteria}
Section contract: .agent-work/sections/{ID}-CONTRACT.md
Required checks: {commands}
Do not broaden scope or fix unlisted speculative issues.
```

### Hard-cap `[tier: plan]` packet (split choice only)

```text
Task: Re-decompose one non-converging section. Do not implement product code.
Working path: {failed_working_path}
Feature plan: .agent-work/PLAN-FULL.md
Feature state: .agent-work/FEATURE-STATE.md
Current failed section: {ID} — {title}
Original section base: {section_base}
Failed tip: {failed_tip}
Backup branch: {backup_branch}
Hard-cap summary and user decision: .agent-work/replans/{ID}-g{generation}-HARD-CAP.md
Review files:
  - .agent-work/reviews/{ID}-SECTION-r01.md
  - .agent-work/reviews/{ID}-SECTION-r02.md
  - .agent-work/reviews/{ID}-SECTION-r03.md

The section failed to reach a clean counting round within three rounds, and the user chose to split.
Split only this section into smaller independently implementable, testable, and reviewable descendants.
Preserve accepted predecessor sections and user-owned feature semantics.
Use hierarchical lineage IDs such as {ID}.1, {ID}.2.
Current lineage depth is {depth}; depth-4+ descendants require a recorded user re-plan choice.
Use the review histories as decomposition evidence: repeated root causes must become explicit boundaries, invariants, oracles, or separate descendants.
Update requirement coverage, dependency edges, downstream Requires, checkpoints, and deferred-work ownership affected by the split.
Do not carry failed implementation choices forward merely because they already exist.
```

### Integration review packet

```text
Review mode: INTEGRATION
Working path: {path}
Feature range: {feature_base}..{feature_head}
Feature contract and requirement matrix: .agent-work/PLAN-FULL.md
Feature state: .agent-work/FEATURE-STATE.md
Section contracts/handoffs: .agent-work/sections/
Review/replan evidence: .agent-work/reviews/, .agent-work/replans/
Focus: full acceptance, cross-section contracts, migration, rollout/rollback,
security, reliability, operations, cleanup, and deferred-work closure.
Output: .agent-work/reviews/FEATURE-INTEGRATION-r01.md
Use: the code-review skill
```

## 3. Tier routing

Map role tiers to the host's available sub-agent tiers (see the Model Routing
Tiers section of the core instructions):

- ordinary section implementation: `[tier: execute]`;
- high-risk section implementation and repairs: `[tier: review]`;
- every counting review round (full round 1, later `DELTA` rounds): a fresh `[tier: review]` reviewer context;
- hard-cap split after a recorded user `split` choice: a clean `[tier: plan]` subagent;
- final integration review when triggered: a fresh `[tier: review]` reviewer context unless governing instructions specify otherwise.

The `[tier: plan]` decomposer is not a generic sixth reviewer. Its task is to change the decomposition, not to continue the same search process.

## 4. Section orchestration algorithm

```text
for section in dependency_order(active_leaf_sections):
    section_base = accepted_predecessor_head(section)
    extract_to_PLAN(section)
    freeze_contract(section, section_base)

    run_implementer(section)
    inspect_repo_and_handoff()
    run_required_checks()
    commit_if_authorized("implementation")

    review_round = 0

    while review_round < 3:
        review_round += 1
        section_head = current_head()
        if review_round == 1 or reset_trigger_fired:
            report = run_full_SECTION_review(
                section_base,
                section_head,
                closed_root_cause_ids=closed_ids(titles_only=True),
                output=f"{section}-SECTION-r{review_round:02d}.md"
            )
        else:
            # After a repair, the counting round is a DELTA review of the
            # repair delta plus its invalidated impact cone; stable scope is
            # never rescanned (see integration-and-convergence.md).
            report = run_DELTA_review(
                repair_base,
                section_head,
                frozen_finding_ids=last_round_material_ids,
                closed_root_cause_ids=closed_ids(titles_only=True),
                output=f"{section}-SECTION-r{review_round:02d}.md"
            )

        findings = main_agent_validate_and_deduplicate(report)

        if findings.require_user_decision():
            persist_state_and_block_for_decision()

        if findings.has_no_new_material_actionable_issue():
            # A clean full round or a delta-verified round accepts the section.
            persist_round_state()
            accept_section_provisionally()
            break

        fixable = findings.agent_fixable_material_items()
        repair_base = section_head
        run_repair(fixable)
        inspect_repo_and_handoff()
        run_relevant_checks()
        commit_if_authorized("repair")
        persist_round_state()

    if not section_is_accepted():
        preserve_failed_attempt(section)
        decision = ask_user_hard_cap_decision(section)
        # continue:     up to two more counting rounds on the same attempt
        # split:        hard_cap_replan(section) -> descendants from original base
        # accept-risk:  accept_with_recorded_debt(section)
        # block:        stop for human intervention
```

### What counts as material

A new `Must Fix`, `Should Fix`, or blocking `Needs Decision` root cause is material.

These normally do not count as material:

- repeated wording of an already-closed root cause;
- explicit work assigned to a later section when the current intermediate state is valid;
- unsupported hypotheses;
- style-only preferences;
- non-blocking `Should Plan` or bounded debt.

The main orchestrator makes this accounting decision from the review report and current evidence.

### Internal repair checks

Targeted internal checks inside a repair wave remain useful for risky fixes. They do not advance `review_round`; the counting round after repair is itself the `DELTA` review.

## 5. Three-round hard cap and user decision

The review-round budget is three counting rounds per active section attempt (full round 1, `DELTA` rounds after repair). There is no soft cap and no autonomous round 4.

If round 3 ends without section acceptance:

1. **Do not run round 4.**
2. Persist the failed attempt and review history.
3. Create `agent-kit/backup/{feature-slug}-{section-id}-g{generation}-{timestamp}` at the failed tip.
4. Compile a round-by-round hard-cap summary with recurring root-cause patterns.
5. Stop and present the user decision: `continue` (up to two more counting rounds), `split`, `accept-risk`, or `block`, in that order, with the current lineage depth attached.
6. Act only on the recorded choice:
   - `continue`: resume counting rounds on the same attempt;
   - `split`: invoke a clean `[tier: plan]` decomposer with the packet above, validate the revised `PLAN-FULL.md`, mark the failed parent `SPLIT_AFTER_HARD_CAP`, activate descendants, and retry them from the failed parent's original `section_base`, not the failed tip; recommend re-planning the feature boundary instead when descendants would be depth `4+`;
   - `accept-risk`: mark `SECTION_ACCEPTED_WITH_DEBT` and record every remaining finding in the deferred-work/residual-risk ledger;
   - `block`: stop for human intervention on the root cause.

### Round-by-round summary

The summary must preserve evidence, not vague “review still found issues” language:

| Round | Mode | Reviewed head | New material findings | Root cause / boundary | Repair commit | Result |
|---|---|---|---|---|---|---|
| 1 | full | `<sha>` | `REV-...` | `<...>` | `<sha>` | findings |
| 2 | delta | `<sha>` | `...` | `...` | `<sha>` | findings/delta-verified |
| 3 | delta | `<sha>` | `...` | `...` | `—` | hard cap |

Also state recurring patterns: contract coupling, ownership ambiguity, too many behaviors, weak oracle, repair-induced interaction, or another evidence-backed cause.

### Decomposition requirements for the `[tier: plan]` decomposer

A valid split must do more than reduce line count. Descendants should separate one or more of:

- behavior outcomes;
- ownership/state boundaries;
- contract introduction vs consumer migration;
- happy path vs risky side-effect path when independently shippable/testable;
- schema expansion vs migration vs contraction;
- policy evaluation vs enforcement integration;
- background production vs consumption/retry behavior;
- enabling refactor vs observable behavior;
- bug-prone interaction classes identified by the review rounds.

Each descendant needs an independent oracle and a stable intermediate repository state.

## 6. Commit and branch discipline

In `EXECUTE_WITH_COMMITS`:

- commit the initial coherent section implementation before its first review;
- after a review with agent-fixable material findings, make one coherent repair commit before the next counting round;
- keep unrelated cleanup/user work out of section commits;
- at hard cap, ensure the failed attempt's section-owned work is committed before making the backup ref;
- the backup branch is created automatically under the skill's delegated authority;
- never push/merge the backup branch automatically.

Recommended messages:

```text
feat(section-S03): implement <behavior>
fix(section-S03): address review round 2 findings
chore(agent): snapshot S03 before hard-cap replan
```

The snapshot commit is only needed when section-owned tracked changes remain. Do not manufacture an empty snapshot commit.

## 7. Worktrees and retry isolation

After hard-cap backup, prefer a new retry branch/worktree rooted at `section_base` instead of resetting the failed branch.

Recommended retry branch:

```text
agent-kit/retry/{feature-slug}-{section-id}-g{next-generation}-{YYYYMMDD-HHMMSS}
```

Rules:

- failed product-code commits remain only in the failed/backup lineage;
- do not cherry-pick them unless the user's hard-cap decision explicitly authorized salvaging verified parts;
- carry forward the revised planning/state artifacts, not failed product-code diffs;
- if unrelated dirty user work exists, leave its worktree untouched and create an isolated retry worktree;
- create retry worktrees under the repository-root `.worktrees/` workspace and register the retry task in `.worktrees/current-agents/` per the manual-git-worktrees skill;
- update `FEATURE-STATE.md` with the new active path/branch.

## 8. Decision handling

### Must block

- required product semantics are undefined;
- two authoritative sources conflict;
- compatibility/migration behavior requires owner choice;
- acceptable risk or rollout policy cannot be inferred;
- the `[tier: plan]` split would require changing a frozen user-owned requirement;
- the three-round review hard cap is reached — the user must choose `continue` / `split` / `accept-risk` / `block`.

### Must not block merely for permission

- a backup branch must be created at the hard cap;
- after a recorded `split` choice, the `[tier: plan]` decomposer must be invoked, the retry branch/worktree created under already delegated execution authority, and the first ready descendant extracted and continued.

## 9. State integrity

Before every handoff, update `FEATURE-STATE.md` with:

- feature branch/worktree and active retry path;
- section ID and lineage;
- section base/current head;
- review round and last review mode;
- review report path and material finding IDs;
- repair commit/check result;
- replan generation;
- hard-cap backup branch/failed tip and the recorded user decision when applicable;
- active descendants and retired parent;
- exact next action.

After context compression, reread `PLAN-FULL.md`, `FEATURE-STATE.md`, and the current `PLAN.md` before continuing.

---
name: sectioned-feature-development
description: "Plan and execute one large, high-risk change as 2-6 reviewable sections with a single plan file, a single state file, one independent review per section, and main-agent verification after repair. Use only when (A) the change crosses a high-risk semantic boundary (persistence/schema, security/permissions, money, time, concurrency/background jobs, public API, shared state ownership) AND is large (roughly 800+ lines of behavioral edits across more than 3 modules); or (B) a previous whole-change implementation or review failed to converge; or (C) the user asks for sectioned development. Size alone or risk alone does not trigger it."
---

# Sectioned Feature Development

Deliver one large feature as a short sequence of bounded sections. Each section is implemented, validated, reviewed once by an independent reviewer, repaired if needed, and verified by the main agent before the next section starts.

## Trigger

Use this workflow only when one holds:

- **A.** The change crosses a high-risk semantic boundary (persistence/schema, security/permissions, money, time, concurrency/background jobs, public API, shared state ownership) **and** is large: roughly 800+ lines of behavioral edits across more than 3 modules.
- **B.** A previous whole-change implementation or review of this work failed to converge.
- **C.** The user asks for it.

Size alone or risk alone does not trigger it. Such changes take the normal path: implement, verify, optionally one `code-review`.

## Authority

Repository-local instructions come first. Fix one mode before touching product code:

- `PLAN_ONLY`: write `.agent-work/PLAN.md` only.
- `EXECUTE_NO_COMMIT`: implement and validate; no branch or commit operations.
- `EXECUTE_WITH_COMMITS`: the core rules' scoped exception authorizes one feature branch plus one commit per section implementation and per repair.

A planning or review request alone does not authorize commits. Never push, merge, open a pull request, rewrite history, reset, clean, or delete user work. Never absorb unrelated uncommitted user changes into a section commit.

Stop for genuinely user-owned decisions: product semantics, compatibility policy, migration meaning, acceptable risk. Do not stop to ask permission for ordinary technical decomposition.

## Artifacts

```text
.agent-work/
├── PLAN.md                        # feature contract + all sections
├── STATE.md                       # live status; update after every step
├── reviews/{section-id}-r{N}.md   # written by the code-review skill
└── plans/{YYYYMMDD-HHMM}.md       # archived PLAN.md after completion
```

State lives in these files, not in chat. After context compaction or on resume, re-read `PLAN.md` and `STATE.md` before doing anything else.

`PLAN.md` template:

```markdown
# {Feature title}

- Outcome: {one sentence}
- Non-goals: {explicitly out of scope}
- Invariants: {truths that must hold in every intermediate and final state}
- Acceptance: {observable, falsifiable criteria}
- Validation: {exact full-suite commands}

## S01 — {title}
- Goal: {one observable behavior increment}
- Depends on: {section IDs or none}
- Scope: {expected files/modules/workflows; what is deferred, and to which section}
- Acceptance: {falsifiable criteria}
- Validation: {exact commands}
```

`STATE.md` template:

```markdown
# State — {feature title}

- Mode: {PLAN_ONLY | EXECUTE_NO_COMMIT | EXECUTE_WITH_COMMITS}
- Branch: {name}    Feature base: {sha}
- Next step: {exactly what to do next}

| Section | Status | Base | Head | Review verdict |
|---|---|---|---|---|
| S01 | pending / in-progress / in-review / accepted / accepted-with-debt / split / blocked | {sha} | {sha} | {clean / findings repaired / ...} |

## Open decisions
## Accepted debt
```

## 1. Plan

1. Inspect repository rules, branch, `git status`, and the build/test entry points. Record the `feature_base` commit.
2. Write the feature contract, then divide the work into **2-6 sections**:
   - Default to vertical slices: one coherent behavior across only the layers needed to make it real and testable.
   - Start with a thin end-to-end skeleton when the integration path is uncertain.
   - Keep an enabling refactor separate from behavior change, and behavior-preserving.
   - For incompatible schema or API changes, sequence expand, migrate, contract; remove the old path last.
   - Do not split by layer, directory, or file type.
3. Plan gate (self-check, no extra reviewer):
   - every acceptance criterion maps to a section;
   - dependencies are explicit and acyclic;
   - each section is independently testable and reviewable without undocumented future work;
   - no section is a "finish/integrate everything" bucket.
4. Present the plan. Resolve open user-owned decisions before code. In `PLAN_ONLY`, stop here.
5. In `EXECUTE_WITH_COMMITS`, create the feature branch. Create `STATE.md`.

## 2. Section loop

Work on exactly one dependency-ready section at a time.

1. **Freeze.** Record `section_base` (current head) in `STATE.md`; mark the section `in-progress`. Implementation must not silently redefine the section's scope or acceptance.
2. **Implement** only this section: a `[tier: execute]` subagent, or `[tier: review]` when the section itself is high-risk. Give it the repository rules, `PLAN.md`, the section ID, and `section_base`. Require the smallest change that meets the acceptance criteria, with meaningful behavior, edge, and error tests.
3. **Validate.** Run the section's validation commands. Do not proceed on failing checks.
4. **Commit** the section when authorized. Record `section_head`.
5. **Review once.** Invoke the `code-review` skill in a fresh `[tier: review]` context:

   ```text
   Review mode: FULL
   Range: {section_base}..{section_head}
   Contract: .agent-work/PLAN.md, section {ID}
   Output: .agent-work/reviews/{ID}-r1.md
   ```

   Do not preload the implementer's reasoning or claims.
6. **Clean** review: mark the section `accepted` and move on.
7. **Findings:** freeze the finding list, then repair only the agent-fixable ones (`[tier: review]`), rerun validation, and commit the repair. The repair agent never declares its own work accepted.
8. **Main-agent verification.** Rerun the checks and re-read the repair diff against each frozen finding: is it closed, and did the repair introduce anything new? Run an independent `code-review` in `DELTA` mode over the repair range (output `{ID}-r2.md`) only when the repair itself touched a high-risk boundary.
9. Verified clean: mark `accepted`. **Still not clean: stop** and ask the user to choose:
   - `continue`: one more repair plus verification;
   - `split`: re-plan this section into smaller sections;
   - `accept-risk`: record the remaining findings under Accepted debt and mark `accepted-with-debt`;
   - `block`: stop for human intervention.

   Present the options with the unresolved findings and evidence. Never discard work or start re-implementation without the user's choice.
10. On `split`: tag the failed head `agent-kit/failed/{section-id}`, mark the section `split`, rewrite it in `PLAN.md` as smaller sections (`S03a`, `S03b`) using the review findings as decomposition evidence, rerun the plan gate, and resume from `section_base`. Reuse failed-attempt code only if the user authorized it.

Update `STATE.md` after every step, including `Next step`.

Run independent sections in parallel only through the `manual-git-worktrees` skill.

## 3. Final gate

1. Run the full validation commands from `PLAN.md`.
2. Run one final `code-review` in `FULL` mode over `feature_base..feature_head`, focused on cross-section composition (contracts between sections, end-to-end paths, migration and rollback), only if a `split` or `accept-risk` occurred or the user asks. Repair findings in bounded scope and verify as in the section loop.
3. Move `PLAN.md` to `.agent-work/plans/{YYYYMMDD-HHMM}.md`. Keep `STATE.md` and `reviews/` as evidence.
4. Report, in Chinese by default:
   - readiness: `mergeable`, `not-mergeable`, or `insufficient-evidence`;
   - section status table, findings repaired, checks run and their results;
   - decisions taken, accepted debt, residual risk;
   - a short maintainability judgment.

## Rules

- One section at a time; never implement future sections early.
- Advance on evidence (passing checks, review file), not on an agent's claim of completion.
- One independent review per section. After repair, the main agent verifies; a `DELTA` review is the exception, not the default.
- Not clean after repair and verification means a user decision, never an autonomous extra round.
- Section acceptance is provisional until the final gate passes.

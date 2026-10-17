# Hard-Cap Replan：<Section ID — Title>

## Failed Attempt

- Feature: `<name>`
- Parent section: `<Sxx / Sxx.n>`
- Parent lineage: `<...>`
- Replan generation: `<n>`
- Original section base: `<commit>`
- Failed tip: `<commit>`
- Backup branch: `agent-kit/backup/<...>`
- Failed working path: `<path>`
- Hard cap: `3 counting review rounds`
- Required acceptance: `a clean counting round (coverage-complete full review or delta-verified)`

## Review Rounds

| Round | Mode | Reviewed head | New material findings | Root cause / boundary | Repair commit | Result |
|---:|---|---|---|---|---|---|
| 1 | full | `<sha>` | `<REV ids / none>` | `<...>` | `<sha / —>` | `findings / clean` |
| 2 | delta | `<sha>` | `<...>` | `<...>` | `<...>` | `<...>` |
| 3 | delta | `<sha>` | `<...>` | `<...>` | `<...>` | `hard-cap / clean` |

## Review Artifacts

- `.agent-work/reviews/<ID>-SECTION-r01.md`
- `.agent-work/reviews/<ID>-SECTION-r02.md`
- `.agent-work/reviews/<ID>-SECTION-r03.md`

## Convergence Diagnosis

- Recurring root-cause classes: <...>
- Coupled ownership/contracts: <...>
- Weak or over-broad oracle: <...>
- Repair-induced interactions: <...>
- Evidence that motivates the split: <...>

## User Decision

- Options presented: `continue / split / accept-risk / block` (lineage depth: `<depth>`)
- Decision: `<continue | split | accept-risk | block>`
- Authorization granted: `<extra rounds (how many) | salvage/cherry-pick scope | risk acceptance scope | none>`
- Remaining findings recorded as debt: `<IDs or none>`

## [tier: plan] Re-decomposition Request

- Split only this parent section.
- Preserve accepted predecessors and user-owned feature semantics.
- Use hierarchical descendant IDs.
- Update requirement coverage, dependency edges, downstream `Requires`, checkpoints, and deferred-work ownership.
- Do not implement product code.
- Do not copy failed implementation structure without re-deriving the boundary from the review evidence.

## Resulting Descendants

| ID | Goal | Depends on | Independent oracle | Review-risk reduction |
|---|---|---|---|---|
| `<Sxx.1>` | <...> | <...> | <...> | <...> |
| `<Sxx.2>` | <...> | <...> | <...> | <...> |

## Retry

- Parent state: `SPLIT_AFTER_HARD_CAP`
- Retry starts from: `<original section base>`
- Retry branch/worktree: `<agent-kit/retry/...>`
- First ready descendant: `<Sxx.1>`
- Failed implementation commits cherry-picked: `no (or the scope authorized in the user decision)`

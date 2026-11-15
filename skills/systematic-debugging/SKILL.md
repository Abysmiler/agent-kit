---
name: systematic-debugging
description: Use when a previous bug fix attempt did not resolve the issue, the user says the bug still happens, a test still fails after one repair round, a second or later debugging pass is starting, or a debugging session is long or repetitive enough to need persistent state across context compaction. Also use when the user asks for systematic or root-cause debugging, or asks to turn .agent-work/debug records and resolved investigations into reusable docs/engineering-notes. Do not use for the first ordinary bug-fix attempt unless explicitly requested or the session is already becoming long-running.
---

# Systematic Debugging

Stop guess-and-patch debugging. Reset to evidence, persist useful state, find the root cause, make one minimal fix, and verify the original symptom. After a hard investigation is resolved, optionally capture what was learned as engineering notes.

## Part 1: Active debugging

### Persistent state

Keep debugging state in `.agent-work/debug/` only when it saves future work: a long or repeated investigation, or one likely to outlive the context window.

```text
.agent-work/debug/
├── INDEX.md       # three tables: Active / Unresolved / Resolved, columns: file | summary
├── active/        # the current investigation
├── unresolved/    # paused or still failing
└── resolved/      # verified fixes
```

In `INDEX.md`, `file` is the relative note path and `summary` says why a future agent should read it. One note per problem:

```md
# <symptom in one line>

- Repro: <smallest command or manual steps>
- Confirmed observations: <facts verified in code, diff, logs, or output>
- Failed approaches: <what was tried, and why it was wrong>
- Current hypothesis: <root cause appears to be X because evidence Y>
- Next diagnostic: <single next check>
- Resolution: <fix and verifying command, once verified>
```

Record confirmed facts only, not speculation or full logs. Before continuing a known problem, and after any context compaction, re-read `INDEX.md` and the relevant `active/` or `unresolved/` note before doing anything else.

### Workflow

1. **Reset to evidence.** Say that this is a systematic pass and that evidence gathering comes next. Inspect the worktree state, the previous attempted fix, the failing command, its full output, and the user's report of what still fails. Treat subagent reports, earlier summaries, and your own assumptions as untrusted until verified in code, diff, logs, or test output.
2. **Recover or create state.** Read `INDEX.md` if it exists. For a long or repeated investigation, create or update one `active/` note and index it.
3. **Reproduce the failure.** Run the smallest command or manual flow that shows the bug. Read the complete error, stack trace, logs, or UI symptom. If it cannot be reproduced locally, name the missing evidence and gather diagnostics instead of guessing.
4. **Trace the root cause.** Check recent diffs. Follow bad data, wrong state, or failing control flow backward to its source. On multi-component paths inspect each boundary: caller to callee, UI to state, API to service, service to persistence, config to runtime. Compare with a similar working implementation in the same codebase; when framework or external API behavior is uncertain, check primary documentation.
5. **Form one hypothesis.** Write it down: "Root cause appears to be X because evidence Y." Test it with the smallest diagnostic or code-reading check. Change one variable at a time; never stack speculative fixes. Update the note when the hypothesis changes.
6. **Establish a failing regression surface.** Prefer an automated test that fails for this bug and checks real behavior. Without a test framework, define the smallest repeatable script or manual repro.
7. **Implement the minimal fix.** Fix the confirmed source of the wrong behavior, not a guard at the symptom. No unrelated refactors, broad rewrites, compatibility layers, or hidden fallbacks. If the direct fix would worsen an oversized module, unclear state owner, or under-tested core path, pause and explain the smallest enabling refactor first.
8. **Verify before claiming progress.** Re-run the original failing command or repro, then the relevant tests, type checks, build, or UI validation. Report exact commands and results; if a check cannot run, state the blocker. Verified: move the note to `resolved/`. Stopped or still failing: move or keep it under `unresolved/`. Update `INDEX.md` either way.
9. **Escalate after repeated failure.** When a pass fails, return to step 1 with the new result instead of layering another fix. After three unsuccessful fix attempts for the same symptom, stop and reassess architecture, state ownership, concurrency, stale assumptions, or test validity with the user before another implementation.

### Subagents

Delegate only bounded, independently verifiable investigation: tracing a call chain, comparing similar implementations, triaging test output. The main agent owns the hypothesis, the fix, the diff review, and verification.

## Part 2: Capture engineering notes

Run this part only when the user asks for it, or when a resolved investigation produced clearly reusable knowledge and the user agrees. It is for stable evidence, not for a live bug.

### Workflow

1. **Inventory the evidence.** Read `INDEX.md` and the relevant notes under `resolved/`, `unresolved/`, and `active/`. If the named issue has no debug record, inspect `git log`, the relevant commit diffs, and nearby historical docs before assuming the evidence is missing. Treat prior summaries as leads; verify them against notes, diffs, logs, tests, or official docs.
2. **Classify each finding.**
   - `docs/engineering-notes/`: transferable knowledge — framework or host behavior the official docs do not cover, debugging methods and decision trees, failure signatures and how to tell similar failures apart, API caveats, validation protocols.
   - Other `docs/` files such as `docs/<topic>-implementation-notes.md`: project-specific material — product behavior, class, function, and parameter names, defaults, local debug flags and paths, current architecture and ownership choices.
   - If a finding needs both, split it and link from the engineering note to the implementation note.
   - Leave concrete debug records in `.agent-work/debug/` as the evidence chain; do not copy whole logs into notes.
3. **Split by failure mode.** One note per independent concern or failure mode. No catch-all notes; cross-link only where it prevents confusion.
4. **Write for the reader's task.** The reader is implementing a similar capability or facing the same class of bug, and must be able to follow the reasoning without reading the original code. Prefer layer contracts, data-flow boundaries, failure signatures, diagnostic commands, and validation surfaces over symbol-by-symbol detail.
5. **Record success and failure.** Give the correct model or fix pattern, and every failed approach with why it was wrong.

### Required note shape

Each substantial file under `docs/engineering-notes/` contains:

- Title.
- `Last updated: <YYYY-MM-DD HH:MM TZ>`.
- `Reference commit: <full git commit hash>`.
- `Observed versions: ...` when behavior depends on a host app, OS, framework, library, SDK, service, model, or tool version.
- Official API or documentation baseline, when external behavior is involved.
- Versioned observations for behavior the official docs do not promise or that contradicts them.
- Layer or module definitions needed to reproduce the reasoning: state ownership, data flow, API or lifecycle boundary, coordinate spaces, or the equivalent for the domain.
- Diagnostic checklist or evidence sources.
- Correct solution or fix pattern.
- `Previous Wrong Attempts`, as the final section: what was tried, why it failed, and how to recognize that failure mode.

### Official documentation

- Do not duplicate official documentation for stable, well-documented behavior. Record only what it omits, leaves ambiguous, or states incorrectly for the observed version.
- Check external behavior against primary sources: official docs, SDK headers, source code, changelogs, issue trackers, or verified local version output.
- Keep the distinction explicit: "Official docs state...", "Observed on <version>...", "This is not guaranteed by the official API...".
- If a version cannot be discovered from the repository or environment, ask the user or mark it unknown. Never present unversioned host behavior as universal.

### Validate and report

- Search `docs/engineering-notes/` for project-specific names, local paths, defaults, and product descriptions; move them out unless they belong to a versioned observation that is useful outside the project.
- Confirm every engineering note has its timestamp and reference commit, and that every documentation gap or contradiction names the observed version.
- Run `git diff --check`. For a documentation-only change, state that code tests were not run for that reason.
- Report: notes created or updated in both locations, evidence sources used, validation commands and results, and remaining unknown versions or evidence gaps.

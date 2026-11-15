# Review Checklist

Load for `Large`-depth reviews, AI-authored changes, and changes to agent tooling, prompts, permissions, or CI. Apply only the lenses the change can actually trigger; every item is a hypothesis to falsify, not an automatic finding. Prioritize by user/business impact, exposure (security, data, money, availability), realistic triggerability, blast radius, and reversibility — never by line count or stylistic dislike.

## Baseline (every non-trivial change)

- The diff implements the stated requirement and nothing unrelated; removed behavior has no remaining users.
- Happy path, invalid/empty input, min/max values, missing data, and partial failure are handled.
- Branch conditions, boolean inversions, off-by-one, defaults, and fallthrough are correct.
- Errors propagate and clean up; nothing is swallowed where correctness matters.
- Units, time zones, locales, currency, rounding, ordering, and serialization are consistent.
- A bug fix has a regression test that fails before the change; assertions check externally meaningful behavior.
- Name the most important untested invariant.

## Domain Semantics

Trigger: business rules, eligibility, calculations, billing, workflows, state transitions.

- Preconditions, postconditions, and legal state transitions match an authoritative source.
- UI, API, domain model, persistence, and downstream integrations agree on meaning.
- Existing stored data and old clients still behave correctly.
- A "fallback" does not silently change business semantics.
- Correctness that depends on an unstated policy choice is `Needs Decision`.

## Data And Persistence

Trigger: schema, migration, query, transaction, cache, serialization, deletion, import/export.

- Old and new application versions can both read and write during a rolling deploy.
- Migration ordering, lock duration, table scans, defaults, nullability, and rollback limits are acceptable.
- Transaction boundaries prevent lost updates, write skew, duplicate writes, and partial side effects.
- Idempotency keys and uniqueness constraints back the application's assumptions.
- No truncation, coercion, precision loss, or irreversible transform.
- Cache invalidation is correct and cache keys are scoped per tenant/user.
- Pagination has stable ordering and bounded batch size.
- Destructive changes and migrations need explicit evidence; a local unit test is not enough.

## State, Async, And Concurrency

Trigger: async work, shared state, jobs, queues, timers, subscriptions, locks.

- Races, stale responses, duplicate submissions, re-entrancy, and out-of-order completion.
- Cancellation and cleanup on timeout, navigation, shutdown, and retry.
- Exactly-once assumptions on at-least-once infrastructure; idempotency across restart and redelivery.
- Lock scope and ordering, deadlock, lease expiry.
- Impossible or ambiguous flag combinations; prefer a transition table when reading gets ambiguous.
- Retry amplification, poison messages, missing backpressure.
- Partial success across database, queue, network, and external services.
- Leaked tasks, handles, sockets, subscriptions, or temp files.

## Security, Privacy, And Trust Boundaries

Trigger: public input, auth, tenants, files, URLs, commands, templates, secrets, logging, webhooks.

- Authentication on every reachable branch; object- and action-level authorization after ID resolution.
- Tenant/user isolation in queries, caches, jobs, and logs.
- Validation at the trust boundary, not only in the UI or caller.
- Injection: SQL/NoSQL, shell, template, path, header, URL, expression.
- SSRF, open redirect, path traversal, archive extraction, unsafe upload or file serving.
- XSS and unsafe Markdown/HTML rendering; CSRF; token scope, lifetime, and replay.
- Secrets or personal data in code, logs, errors, telemetry, artifacts, or frontend bundles.
- Fail-open behavior and swallowed security errors; missing rate limits on costly or enumerable operations.
- Anchor each finding to an asset, attacker capability, reachable path, and impact.

## Reliability, Operations, And Release

Trigger: deploy, config, flags, retries, health checks, logging, migrations.

- Config defaults and behavior with missing or invalid values.
- Deployment ordering between application, schema, queues, and external contracts.
- Rollback remains feasible after writes or migrations.
- Timeout budgets, retry limits with jitter, overload behavior.
- Feature-flag lifecycle, kill switch, and behavior when the flag service fails.
- Logs/metrics/alerts exist for the changed critical path and do not leak secrets.

## Performance And Cost

Report only with plausible scale or observed evidence.

- N+1 queries, repeated remote calls, unbounded fan-out or loops over unbounded data.
- Missing pagination, streaming, or batching; payload and memory growth.
- Token, model, compute, storage, and third-party quota amplification.

## Architecture And Maintainability

- Dependency direction; no bypass of an established boundary or policy layer.
- Single source of truth for domain state, validation, errors, and configuration.
- Duplicate helpers, parallel service layers, near-identical components.
- Interfaces, factories, or config with one real use and no high-risk reason.
- Does the fix make the next similar change easier, or add another exception?

## Dependencies And Supply Chain

Trigger: manifest, lockfile, build scripts, containers, CI actions, plugins, vendored code.

- The dependency is necessary; stdlib or an installed package does not already cover it.
- Package name, registry, version, license, and maintenance are verified from an authoritative source.
- Typosquatting, mutable tags, unpinned actions/images, install scripts.

## Tests And CI Integrity

- The test fails before the change and passes after it.
- Assertions check real outcomes, not mocks, call counts, or snapshots alone.
- Over-mocking that lets an impossible system pass; no integration coverage at the changed boundary.
- Removed or skipped tests, lowered thresholds, narrowed commands, `|| true`, `continue-on-error`, changed triggers or path filters.
- Treat weakened validation as blocking unless equivalent protection replaces it.
- For high-risk pure logic, consider property, metamorphic, differential, or state-machine tests.

## UI And Workflow

Trigger: UI, forms, routing, localization, user-facing errors.

- Loading, empty, error, disabled, submitting, stale, and offline states.
- Double submission, optimistic updates, cancellation on navigation.
- Client and server validation agree; destructive actions are confirmed or undoable.
- Inspect actual rendered behavior when the repository supports it.

## AI-Authored Change Patterns

The risk is the observed pattern, not who wrote it; never infer authorship from style.

| Pattern | Signals | Check |
|---|---|---|
| Plausible but wrong semantics | Invented defaults or rules; summary more certain than evidence | Trace one critical workflow end to end; ambiguity becomes `Needs Decision` |
| Scope expansion | Files with no path to the goal; unrequested cleanup, upgrades, "for completeness" branches | Require a reason for every changed area |
| Compatibility theater | Fallbacks, aliases, dual paths with no real consumer; fallback that guesses | Identify actual consumers; prefer removal |
| Local-optimum patch | Bypasses shared policy/validation/state layer; copied permission check; special-case branch | Find the canonical entry point; fix the root cause |
| Reuse blindness | New helper duplicating existing behavior; second source of truth | Search by concept and data shape, not only by name |
| Accretion and premature abstraction | Wrapper chains, flag piles, one-implementation interfaces, unused config | Ask what can be deleted or collapsed |
| Test-target overfitting | Literal special cases matching fixtures; narrow conditionals | Probe with new boundary and adversarial inputs |
| Weak oracle / reward hacking | Tests, fixtures, or thresholds changed with the code; checks skipped or narrowed | Inspect what changed in the validation environment |
| Hallucinated API or config | Names that appear only in the diff; mixed-version APIs; fallback masking the failure | Verify against installed versions and local definitions |
| Fabricated dependency | Obscure or misspelled package; large transitive churn | Verify source, necessity, and provenance |
| Error swallowing | Broad catch returning a default; security or data failure becomes "not found" | Confirm fail-open vs fail-closed from requirements |
| Stale state | References to missing files/symbols; test claims from an earlier head | Reconcile `git status`, head, and evidence |
| Premature completion | "Should work" with no observed run; services never started | Verify external behavior at the current head |
| Documentation drift | Generated docs or plans disagree with executable behavior | Identify the source of truth and regeneration path |

## Agent And Automation Changes

Trigger: prompts, skills, rule files, hooks, workflows, model calls, MCP, connectors, sandbox.

- Untrusted content (issues, PR text, web pages, tool output, logs) flowing into prompts or tool decisions.
- Tool, network, token, and deployment permissions broader than the task needs.
- Model output executed as shell, SQL, code, or a destructive action without schema, allowlist, or approval.
- The agent can edit its own rules, tests, scanners, permissions, or completion criteria.
- Secrets or sensitive data sent to prompts, transcripts, logs, or published artifacts.
- No iteration, cost, or time budget; reviewer/fixer ping-pong; non-idempotent external actions.
- Author, reviewer, and fixer sharing one context are not independent evidence.

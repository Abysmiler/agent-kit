# Audit Coverage Checklist

Use this as a menu, not a questionnaire. Pick the domains that apply to the system and the run's scope, then turn the listed items into concrete failure hypotheses and check them against current code and evidence.

## How to sample

Prioritize areas with: high business, security, data, or availability criticality; high churn or defect history; broad fan-in/fan-out; public inputs, privileged actions, or irreversible side effects; weak tests or observability; new dependencies, migrations, or platform changes; past findings.

Evidence strength, strongest first: reproduced behavior or runtime evidence; checks executed against the current head; concrete code, configuration, and data-flow reading; repository docs and contracts; version history; agent or human summaries (always verify).

A finding has evidence of a defect or control weakness. A gap means evidence was insufficient to conclude; record it as next focus, not as a defect. A clean scan is not proof of safety.

## Domains

### Business correctness

- End-to-end critical user and operator workflows; domain invariants and legal state transitions.
- Money, units, dates, time zones, quotas, ordering, eligibility.
- Defaults, empty and boundary values, legacy records, invalid transitions.
- Error, cancel, retry, timeout, partial-completion, and duplicate-request behavior.
- Rules that exist only in code or in people's heads; operator tools that bypass normal validation.

### Architecture and ownership

- Module boundaries, dependency direction, cycles, god modules, cross-cutting entry points.
- State ownership: one authoritative writer per piece of state, or many.
- Public APIs, events, schemas: versioning and compatibility.
- Whether code, docs, and runtime topology agree.
- Whether the next likely change gets easier or more fragile.

### Identity, authorization, and isolation

- Authentication, session creation, rotation, expiry, revocation, account recovery.
- Object-level and action-level authorization; tenant, organization, and user isolation.
- Authorization in background jobs, caches, exports, webhooks, and admin tooling.
- Central enforcement versus bypass paths; default-deny versus fail-open; service credential scope.

### Input, output, and secrets

- Validation at trust boundaries.
- Injection: SQL, shell, template, path, deserialization, code execution.
- SSRF, redirects, file upload/download, path traversal, archives, symlinks.
- Output encoding, XSS, untrusted rich text; cryptography use, randomness, signature verification.
- Secrets in code, logs, errors, telemetry, build artifacts, frontend bundles; rotation and scope.
- Sensitive data: minimization, retention, deletion, masking in logs.
- Rate limits, enumeration, expensive operations, abuse paths.

### Data lifecycle and persistence

- Schema constraints, indexes, nullability, referential integrity.
- Migrations: locking, backfill, mixed-version compatibility, rollback. A migration passing on an empty database proves little.
- Transactions, isolation, lost updates, partial writes.
- Cache keys, invalidation, tenant scope, stale data.
- Derived state and reconciliation between stores.
- Encoding, precision, time zones, irreversible transforms.
- Backups: restore evidence, not just existence.

### Concurrency, jobs, and distributed state

- Shared mutable state, locks, races, re-entrancy, out-of-order completion.
- Queue delivery semantics, idempotency, deduplication, poison messages.
- Retries: classification, backoff, limits, side-effect safety, retry storms.
- Cancellation, timeouts, shutdown with in-flight work.
- Scheduler overlap, missed or duplicate runs; state machines versus accumulated boolean flags.

### Reliability and operations

- Timeouts, circuit breaking, graceful degradation, load shedding.
- Startup, readiness, health, and shutdown behavior.
- Logs, metrics, alerts for critical workflows: actionable and owned.
- Recovery paths: stuck jobs, failover, restore, kill switches. Verify recovery, not only normal operation.

### Release, configuration, and change safety

- Configuration sources, defaults, validation, precedence; secrets separated from config.
- Feature flags: failure behavior, expiry, cleanup.
- CI/CD triggers, permissions, required checks, branch protection. Inspect the effective workflow, not YAML intent.
- Application/database sequencing, rollback after irreversible writes.

### Performance, capacity, and cost

- Unbounded inputs, algorithmic complexity, N+1 access, missing pagination.
- Query plans and indexes; fan-out and payload size.
- Memory, connections, file handles, storage growth; third-party quotas and cost; model token use in agent features.
- Tie findings to realistic volume; skip speculative micro-optimization.

### Supply chain and build integrity

- Dependency inventory, maintenance status, licenses, end-of-life runtimes.
- Lockfiles, pinning, mutable tags, install scripts, typosquatting, dependency confusion.
- Dependencies that do not exist, were hallucinated, or are trivially replaceable.
- Vulnerability reachability and remediation path.
- CI runner token scope, cache poisoning, artifact provenance.
- Third-party agent tools, MCP servers, plugins, skills, and remote instructions.

### Tests and verification

- Portfolio, not coverage percentage: unit, integration, end-to-end, migration, permission and negative tests, concurrency tests.
- Oracles that assert real outcomes versus tests that only execute code or mirror the implementation.
- Mock balance, fixture realism, flakiness, order dependence; critical workflows with no automated check.
- Deleted, skipped, or weakened tests and suppressed scanners in history.

### Maintainability and anti-bloat

- Complexity and churn hotspots; areas nobody can explain.
- Duplicate helpers, parallel abstractions, inconsistent patterns.
- Stale docs, missing rationale for non-obvious decisions, tacit knowledge.
- Simplification ladder, in order: does it need to exist; does the standard library do it; does the platform do it natively; does an installed dependency do it; can it be one smaller local block.
- Candidates: dead code, unused config, speculative features, wrapper-only files, one-implementation interfaces, one-product factories, layers with one caller, obsolete compatibility paths.
- Never recommend deleting trust-boundary validation, data-loss prevention, security controls, migration safeguards, accessibility basics, meaningful tests, or real operational knobs to reduce line count. Rank by safe systemic benefit, not deleted lines.

### UI and user operations (when applicable)

- Loading, empty, error, stale, and disabled states; duplicate submission and stale responses.
- Destructive actions: confirmation, undo, visible scope; client/server validation consistency.
- Keyboard access, focus, labels, contrast; localization of dates, numbers, currency, long text.

### AI-agent risks (when agents write, review, deploy, or operate the system, or the system ships agent features)

Codebase effects of agent authorship:

- Architecture erosion: each change adds branches, flags, wrappers, and local exceptions while narrow checks keep passing.
- Local fixes near the caller instead of at the shared validation, policy, or data boundary; the same defect recurs in sibling workflows.
- Weak existing patterns copied as if endorsed (broad catches, ad hoc retries, unsafe parsing).
- Verbose surface: speculative config, redundant layers, new dependencies for trivial functions.
- Tests that assert the implementation rather than the requirement; passing checks reached by weakening the check.
- Code volume outpacing anyone's understanding of intent and invariants.

Agent control plane:

- Prompt injection: untrusted issues, docs, web pages, logs, tool output, or dependency metadata reaching model context as instructions.
- Tool scope: generic shell, filesystem, database, or cloud access where a narrow tool suffices; production access from development contexts.
- Autonomy: irreversible, privileged, financial, or customer-visible actions without accountable approval; no kill switch or budget.
- Self-modifying guardrails: the agent can edit its own rules, permissions, hooks, tests, or scanners and then rely on them.
- Model output flowing into shell, SQL, code execution, or deployment without validation.
- Local control planes: unauthenticated localhost services or sockets that trigger privileged actions.
- Memory and state: stale progress files, cross-session contamination, poisoned memory, premature "done" claims.
- Unbounded loops and retries; same model as author, reviewer, and fixer with no independent check.
- Instruction files: stale, contradictory, or so long they are ignored; rules that exist outside the repository.

## Choosing a durable control

- Wrong semantics: authoritative spec, examples, recorded user decision.
- Local duplication: one canonical entry point plus a structural lint or test.
- Weak validation: stronger oracle; integration, property, or recovery test.
- Injection and tool abuse: trust separation, least privilege, narrow typed tools, approval gates.
- Architecture erosion: structural tests, explicit state models, small recurring cleanup.
- Supply chain: pinning, allowlists, scanning, provenance. Unbounded loops: budgets and stop conditions.

A control should be enforceable, observable, and owned. Documentation alone is not enough for a high-impact invariant.

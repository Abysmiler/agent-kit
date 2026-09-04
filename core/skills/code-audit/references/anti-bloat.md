# Anti-Bloat Audit Focus

Use this reference when the audit request mentions over-engineering, bloat, de-bloat, unnecessary complexity, unnecessary dependencies, "what can we delete", YAGNI, or a repo/module getting too large.

Source discipline:

- Derive this focus from the repository's own largest existing skills and their review/audit conventions.
- Do not derive full audit behavior from small-review derivatives of this skill.
- Do not turn the full audit into code golf. The rule is "lazy means efficient, not careless."

Apply this ladder during the simplification pass:

1. Does this need to exist at all?
2. Does the standard library do this?
3. Does a native platform feature cover it?
4. Does an already-installed dependency solve it?
5. Can the same behavior be expressed in one straightforward line or one smaller local block?
6. Only then recommend the minimum new code or abstraction.

Use these anti-bloat tags in `FULL.md` findings and in the Chinese `REPORT.md` when relevant:

- `delete`: dead code, unused flexibility, speculative features, redundant compatibility paths, wrappers that only delegate, or files exporting one trivial thing.
- `stdlib`: hand-rolled functionality already provided by the language, runtime, framework, or database.
- `native`: dependency or custom code doing what the platform already provides, such as browser controls, CSS, DB constraints, or built-in formatting.
- `yagni`: interface with one implementation, factory with one product, config nobody sets, layer with one caller, or scaffolding "for later".
- `shrink`: same behavior with fewer files, fewer branches, fewer states, or a clearer local expression.
- `reuse`: a parallel abstraction where the established project entry point should be extended instead.

Rank anti-bloat findings by the largest safe reduction first, but keep safety boundaries above line count. Never recommend deleting trust-boundary validation, data-loss prevention, security controls, accessibility basics, migration safeguards, meaningful tests, explicitly requested behavior, or real-world calibration/configuration knobs.

When an intentional shortcut is acceptable but has a known ceiling, recommend a tracked debt marker with the ceiling and revisit trigger instead of pretending it is universally correct.

# Pedro Organiza — Architectural Decisions

This document records the major architectural decisions behind Pedro Organiza.

It exists to:

* Preserve design intent
* Prevent accidental architectural drift
* Help future maintainers understand *why*, not just *what*
* Provide historical context for tradeoffs

Pedro favors **determinism, safety, and operator control** over convenience or automation magic.

Only decisions with long-term structural impact belong here.

---

## ADR-000 — Pedro Is a Deterministic Library Engine

**Status:** Accepted
**Version:** 0.8.0

### Decision

Pedro will compute filesystem actions from database state in a deterministic manner.

The same database state must always produce the same filesystem result.

### Why

Music libraries are high emotional-value datasets.
Unexpected behavior destroys trust instantly.

Determinism makes Pedro predictable and therefore safe.

### Consequences

* No hidden automation
* No heuristic filesystem mutations
* Preview-before-apply becomes mandatory
* Database becomes the single source of truth

### Alternatives Rejected

* Automation-first design (beets-style)
* Heuristic guessing
* Silent corrections

Pedro behaves like a surgical instrument — not an autopilot.

---

## ADR-001 — Preview Is Mandatory Before Apply

**Status:** Accepted
**Version:** 0.8.0

### Decision

Filesystem mutations must always be previewable.

Apply is never the first step.

### Why

Operators must understand the blast radius before execution.

This is especially critical for large libraries.

### Consequences

* Dedicated `pedro preview` command
* `--dry-run` support
* Execution engine separated from planning

Safety is the default posture.

---

## ADR-002 — Schema Must Evolve Without Destroying Data

**Status:** Accepted
**Version:** 0.8.0

### Decision

Database migrations must be additive and non-destructive.

Full rescans should not be required after upgrades.

### Why

Large libraries can take hours or days to analyze.

Forcing rescans punishes committed users.

### Consequences

* Schema-safe migrations
* Column additions instead of destructive rewrites
* Backwards-compatible evolution

Pedro respects the operator’s time.

---

## ADR-003 — Deletion Must Be Explicit and Guarded

**Status:** Accepted
**Version:** 0.8.0

### Decision

Permanent deletion requires explicit operator confirmation.

Default behavior is quarantine.

Large delete operations require typing `DELETE`.

### Why

Accidental deletion is unrecoverable trust damage.

Pedro assumes the library is valuable.

### Consequences

* Multi-step confirmation
* Lock protection
* Defensive filesystem posture

Safety is prioritized over speed.

---

## ADR-004 — CLI Is a First-Class Interface

**Status:** Accepted
**Version:** 0.8.0

### Decision

Pedro must be fully operable without a graphical UI.

The CLI is not a fallback — it is a primary interface.

### Why

Power users, servers, NAS deployments, and automation workflows require headless operation.

UI layers may evolve.
The CLI must remain stable.

### Consequences

* Clear command namespaces (`db`, `preview`, `apply`)
* Operator-oriented vocabulary
* Scriptable behavior

Pedro is infrastructure-grade software.

---

## ADR-005 — Pedro Is Not Competing With Beets

**Status:** Accepted
**Version:** 0.8.0

### Decision

Pedro positions itself as a deterministic restructuring engine — not an automation-heavy tagger.

### Why

Automation tools optimize for convenience.
Pedro optimizes for control and predictability.

These tools serve different operator personalities.

### Consequences

* Fewer "magic" behaviors
* More explicit workflows
* Higher operator trust

Pedro is designed for people who fear data loss.

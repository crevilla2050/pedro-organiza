# Pedro Doctor — Architecture & Design Spec

## Purpose

`pedro doctor` is a diagnostic command that validates the structural health of a Pedro installation.

It ensures that:
- The database schema is consistent
- Required tables and columns exist
- Subsystems (dupes, taxonomy, reports) are bootstrappable
- The environment is safe to operate on before running heavy commands

This command is designed to prevent runtime failures and improve user trust.

---

# Goals

## Primary Goals

1. Prevent runtime crashes caused by missing schema pieces
2. Provide actionable diagnostics for users
3. Detect drift between:
   - Code expectations
   - Database reality
4. Enable safe upgrades across versions

## Secondary Goals

- Serve as a support/debug tool
- Provide structured output for bug reports
- Become a future CI validation tool

---

# Non-Goals

- Automatic destructive repairs
- Silent schema mutations (unless explicitly requested)
- Deep performance profiling

Doctor diagnoses first. Fixes are opt-in.

---

# Command UX

## Basic Usage

```bash
pedro doctor
```

Output style: human-readable report.

---

## JSON Mode (for support)

```bash
pedro doctor --json
```

Returns structured diagnostics for:
- GitHub issues
- Bug reports
- Future telemetry (local-only)

---

## Auto-Fix Mode (future-safe)

```bash
pedro doctor --fix
```

Runs only safe, additive repairs:
- Missing views
- Missing columns
- Report directories

Never drops or mutates data.

---

# Output Design

## Human Output Example

```
Pedro Doctor Report
===================

[OK] Database reachable
[OK] Schema version: 6 (up to date)
[OK] Core tables present
[WARN] Missing alias views (dupes may be incomplete)
[OK] Taxonomy tables present
[OK] Reports directory writable

Summary: 1 warning, 0 errors
```

Severity levels:
- OK
- WARN
- ERROR

---

# Diagnostic Categories

## 1. Database Connectivity

Checks:
- DB file exists
- SQLite readable
- Write permissions

Errors:
- Missing DB
- Locked DB

---

## 2. Schema Version Integrity

Checks:
- `pedro_environment` exists
- `schema_version` readable
- Matches TARGET_SCHEMA_VERSION

Cases:
- Lower version → WARN (suggest migrate)
- Higher version → ERROR (newer DB than code)

---

## 3. Core Tables Validation

Required tables:
- files
- actions
- pedro_environment

Optional but expected:
- libraries
- file_library_map

Missing core tables = ERROR.

---

## 4. Column Drift Detection

This solves your recent fires 🔥

Check expected columns like:
- files.detected_container
- files.presence_state
- genres.created_at
- genres.source

If missing:
- WARN (fixable via migrate)

Implementation:
- Reuse schema helper registry

---

## 5. Taxonomy Health

Checks:
- genres table exists
- genre_mappings exists
- file_genres exists

Also validates columns:
- created_at
- source
- confidence

Failures here caused your recent crashes.

---

## 6. Alias / Dupes Bootstrap

Checks:
- alias views exist
- build_duplicate_clusters() can run safely

Method:
- Run dry clustering in try/except

If fails → WARN (not fatal to whole system)

---

## 7. Reports System

Checks:
- ~/.config/pedro exists
- reports directory writable

Future-proof paths:
- reports/dupes
- reports/taxonomy
- reports/blueprints

---

## 8. Filesystem Permissions

Checks:
- Source root accessible (if configured)
- Library root writable (if configured)

These come from pedro_environment.

---

## 9. Dependency Checks (Soft)

Optional tools:
- ffmpeg / fpcalc

Reported as INFO, not warnings.

---

# Internal Architecture

## Module Layout

```
backend/doctor/
  doctor_runner.py
  checks/
    db_checks.py
    schema_checks.py
    taxonomy_checks.py
    dupes_checks.py
    reports_checks.py
```

Each check returns a structured record.

---

# Diagnostic Record Format

Internal structure:

```python
{
  "id": "taxonomy.tables",
  "status": "WARN",
  "message": "genre_mappings missing",
  "hint": "Run pedro migrate",
  "auto_fix": "migrate"
}
```

This allows:
- Pretty CLI output
- JSON export
- Future UI integration

---

# Auto-Fix Strategy

Auto-fix is deliberately conservative.

Allowed fixes:

### Safe
- Create missing views
- Create report directories
- Run ensure_* schema helpers

### Not allowed
- Data mutation
- Deleting anything
- Rebuilding clusters

---

# CLI Wiring

Add new namespace in CLI:

```
pedro doctor
pedro doctor --json
pedro doctor --fix
```

Placement:
- Top-level command (not subcommand)
- Same tier as `status`

Reason: onboarding tool.

---

# Integration Points

## 1. Pre-flight Hook (future)

Commands like:
- analyze
- apply

Could optionally run a light doctor check.

Example:

```
Running pre-flight checks...
[WARN] Schema drift detected
```

---

## 2. GitHub Issue Template

Doctor JSON output can be pasted into issues.

Huge support multiplier.

---

## 3. UI Integration (0.9+)

Future dashboard card:

```
System Health: 92%
```

---

# Implementation Order

## Phase 1 (0.8.4)

- DB connectivity
- Schema version check
- Core tables
- Column drift detection
- Taxonomy tables

This already eliminates most runtime crashes.

---

## Phase 2 (0.8.5)

- Dupes bootstrap validation
- Reports directory checks
- Filesystem permission checks

---

## Phase 3 (0.9+)

- Auto-fix mode
- JSON schema export
- UI health panel

---

# Risks

## Over-engineering

Doctor must stay lightweight.
No ORM.
No reflection magic.

Just deterministic checks.

---

## False alarms

Avoid noisy warnings.
Each warning should be actionable.

---

# Success Criteria

You know doctor is successful when:

- Reddit install issues drop
- Migration bugs surface earlier
- Users paste doctor output in issues
- You stop debugging schema manually 😄

---

# Philosophy Alignment

Doctor is not just a tool.
It reinforces Pedro’s identity:

Deterministic
Transparent
Operator-first

It makes Pedro feel like a professional system.

And that’s exactly where the project is heading.


---

# Phase 1 — Implementation Checklist (Pedro 0.8.4)

This translates the doctor architecture into concrete build steps.
Goal: ship a useful `pedro doctor` in 0.8.4 with minimal risk.

---

## Scope of Phase 1 (0.8.4)

**Ship only high-signal checks:**

1. Database schema integrity
2. Required tables present
3. Lock file detection
4. Actions table sanity
5. Alias clustering readiness

Everything else becomes Phase 2+.

---

# 1. Module Layout

Create a new backend package:

```
backend/doctor/
    __init__.py
    doctor_runner.py
    checks/
        __init__.py
        db_schema.py
        lock_state.py
        actions_sanity.py
        alias_health.py
```

Keep checks small and pure.
No side effects.

---

# 2. Core Runner

## File

`backend/doctor/doctor_runner.py`

## Responsibilities

- Register checks
- Execute them in deterministic order
- Aggregate results
- Produce summary

## Output Contract

Each check returns:

```
{
  "id": "db.schema",
  "status": "ok|warn|fail",
  "message": "Human readable",
  "details": {...optional}
}
```

---

# 3. Check Definitions

## 3.1 DB Schema Check

File: `checks/db_schema.py`

### Verifies
- pedro_environment exists
- schema_version readable
- schema_version == TARGET

### Fail Conditions
- Missing environment table
- schema_version mismatch

---

## 3.2 Required Tables Check

Also inside `db_schema.py`

Tables to verify:

- files
- actions
- genres
- file_genres
- genre_mappings

Missing table → FAIL

---

## 3.3 Lock File Check (IMPORTANT)

File: `checks/lock_state.py`

Reuse existing apply lock mechanism.

Expected behavior:

- If lock file exists → WARN
- If stale lock (older than X hours) → WARN + hint

No new locking logic.
Just detect.

---

## 3.4 Actions Table Sanity

File: `checks/actions_sanity.py`

Checks:

- actions table exists
- no rows stuck in "executing"
- no orphaned file_id references

Warn if anomalies found.

---

## 3.5 Alias Clustering Readiness

File: `checks/alias_health.py`

Goal: prevent "alias_strong_edges missing" regressions.

Checks:

- alias views can be built (call ensure_alias_views)
- build_duplicate_clusters does not throw

Failure → actionable error.

This directly protects the dupes feature.

---

# 4. CLI Integration

Add new command:

```
pedro doctor
```

### Flags (Phase 1 minimal)

```
--json        machine readable
--strict      non-zero exit on warnings
```

Future flags:
- --fix
- --verbose

---

# 5. Output Design

## Human Mode (default)

Example:

```
Pedro Doctor — System Health Check

[OK] Database schema is current (v6)
[OK] Core tables present
[WARN] Lock file detected (possible interrupted apply)
[OK] Actions table sane
[OK] Alias clustering operational

Summary: 4 OK, 1 WARN, 0 FAIL
```

---

## JSON Mode

Machine readable for:
- CI
- GitHub issues
- Future telemetry

```
pedro doctor --json
```

---

# 6. Exit Codes

Important for scripting.

| Condition | Exit Code |
|----------|----------|
| All OK | 0 |
| Warnings only | 0 (or 1 in strict mode) |
| Any FAIL | 2 |

---

# 7. Testing Strategy

## Unit Tests

- Fake SQLite DB with missing tables
- Simulated stale lock file
- Alias failure injection

## Manual Tests

1. Fresh DB
2. Corrupted DB
3. Interrupted apply
4. Old schema DB

---

# 8. Non-Goals (0.8.4)

Do NOT include yet:

- Auto-fix mode
- Filesystem scanning
- Performance metrics
- Doctor plugins

Keep it lean and trustworthy.

---

# 9. Future Expansion Hooks

Design runner to allow:

```
register_check(id, fn, phase="core")
```

This enables:
- Plugin ecosystem
- Community diagnostics
- UI health panel

---

# 10. Website Note (Future)

Planned additions (post-1.0 era):

- Contributors page (with humor)
- Support/donation transparency
- Community recognition

This aligns with Pedro's human-first philosophy.

---

# Implementation Readiness

Pedro is now mature enough to justify a built-in diagnostic layer.

Shipping `pedro doctor` in 0.8.4 will:

- Reduce GitHub support load
- Increase user confidence
- Enable better bug reports
- Strengthen long-term maintainability

This is a leverage feature, not a cosmetic one.


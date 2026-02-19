# Pedro Doctor — CLI Specification

## Status

Draft for 0.8.4
Contract-first design

---

# Overview

`pedro doctor` is Pedro Organiza’s diagnostic and observability command.

It provides structured health checks for:

* Database schema integrity
* Filesystem sanity
* Configuration validity
* Lock safety
* Operational consistency

Doctor is designed to be:

* Deterministic
* Fast by default
* Extensible
* Scriptable
* Future UI-compatible

---

# Design Goals

1. **Fast default check**

   * Running `pedro doctor` should take <1 second on most systems.

2. **Human-first output**

   * Clear PASS / WARN / FAIL semantics.

3. **Machine-readable mode**

   * JSON output for CI, scripts, and UI.

4. **Composable diagnostics**

   * Individual diagnostic scopes can be run independently.

5. **Future extensibility**

   * Architecture supports plugins and self-healing (`--fix`).

---

# Command Syntax

```
pedro doctor [scope] [options]
```

If no scope is provided, the default scope is `quick`.

---

# Scopes

## quick (default)

```
pedro doctor
pedro doctor quick
```

Fast health snapshot.

Checks:

* Database reachable
* Schema version readable
* Core tables exist
* Active config readable
* Lockfile sanity (light)

Target runtime: <1s

---

## tables

```
pedro doctor tables
```

Schema integrity diagnostics.

Checks:

* Required tables exist
* Required columns exist
* Missing migrations detected
* Alias views present
* Genre tables present

This scope detects:

* Partial migrations
* Manual schema edits
* Upgrade drift

---

## db

```
pedro doctor db
```

Relational integrity checks.

Checks:

* Orphaned foreign keys
* Files without libraries
* Dangling file_genres links
* Invalid lifecycle states
* Duplicate SHA clusters

This is heavier than `tables`.

---

## fs (filesystem)

```
pedro doctor fs
```

Filesystem environment validation.

Checks:

* Source roots exist
* Library root writable
* Quarantine folder valid
* Broken symlinks
* Missing mounted drives

---

## config

```
pedro doctor config
```

Configuration validation.

Checks:

* config.json integrity
* Required keys present
* Path normalization
* Deprecated fields
* Environment overrides

---

## locks

```
pedro doctor locks
```

Lock and concurrency diagnostics.

Checks:

* Stale lock files
* PID mismatch
* Interrupted apply detection
* Zombie operations

Uses existing Pedro lockfile system.

---

## all

```
pedro doctor all
```

Runs all diagnostic scopes in sequence.

Intended for:

* Bug reports
* CI validation
* Release testing
* Advanced users

Runtime depends on library size.

---

# Options

## --json

```
pedro doctor all --json
```

Outputs structured JSON.

Use cases:

* CI pipelines
* GitHub issue attachments
* Future UI integration

---

## --strict

```
pedro doctor all --strict
```

Exit with non-zero code if ANY warnings or failures occur.

Exit codes:

* 0 → all checks passed
* 1 → warnings present
* 2 → failures present

---

## --report <path>

```
pedro doctor all --report doctor_report.json
```

Writes JSON report to file.

If omitted, Pedro may auto-generate timestamped reports in:

```
~/.config/pedro/reports/doctor/
```

---

# Output Semantics

Doctor outputs structured diagnostic entries:

Human-readable mode:

```
[PASS] Database reachable
[PASS] Core tables present
[WARN] Missing genre_mappings table
[FAIL] Library root not writable
```

Summary footer:

```
Doctor summary:
  PASS: 5
  WARN: 1
  FAIL: 1
```

---

# JSON Output Format

Top-level structure:

```json
{
  "doctor_version": 1,
  "timestamp": "2026-02-18T05:21:00Z",
  "scope": "all",
  "summary": {
    "pass": 12,
    "warn": 2,
    "fail": 1
  },
  "checks": [
    {
      "id": "schema.tables_exist",
      "severity": "PASS",
      "message": "Core tables present"
    },
    {
      "id": "locks.stale_lock",
      "severity": "WARN",
      "message": "Lockfile older than 24h"
    }
  ]
}
```

This format is:

* Stable
* Versioned
* UI-compatible
* Diff-friendly

---

# Severity Levels

Doctor uses three severity levels:

| Level | Meaning            |
| ----- | ------------------ |
| PASS  | Healthy            |
| WARN  | Non-critical issue |
| FAIL  | Blocking problem   |

Future versions may introduce:

* INFO
* SUGGESTION

---

# Exit Codes

| Code | Meaning               |
| ---- | --------------------- |
| 0    | All checks PASS       |
| 1    | WARN present          |
| 2    | FAIL present          |
| 3    | Internal doctor error |

These codes are stable API contracts.

---

# Internal Architecture (Non-Normative)

Doctor is implemented as a registry of checks:

```python
DoctorCheck(
    id="schema.tables_exist",
    scope="tables",
    cost="low",
    runner=check_tables,
)
```

Scopes are logical groupings over registered checks.

This enables:

* Plugin checks
* UI dashboards
* Incremental diagnostics

---

# Non-Goals (0.8.x)

Not included yet:

* Automatic repair (`--fix`)
* Background monitoring
* Telemetry
* Remote diagnostics

These are 0.9+ candidates.

---

# Future Extensions

Planned evolutions:

* `pedro doctor --fix`
* UI health dashboard
* Plugin diagnostics
* Docker healthcheck mode
* GitHub issue auto-bundling

---

# Stability Guarantees

The following are considered stable contracts:

* CLI grammar
* Scope names
* JSON schema versioning
* Exit codes

Breaking changes will only occur in major versions.

---

# Philosophy

Doctor exists to reduce fear.

Large music libraries are fragile and valuable.
Users deserve visibility into system health before taking action.

Doctor is Pedro’s safety introspection layer.

Knowledge first. Actions later.

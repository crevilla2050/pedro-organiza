# Changelog
Pedro follows semantic versioning.
Breaking changes will always be clearly documented.

## [0.8.3] — Deterministic Duplicate Clustering & Advisory Intelligence

This release introduces Pedro’s first complete duplicate clustering engine and expands the system from deterministic execution into deterministic analysis.

Pedro can now identify duplicate groups across large libraries and suggest a primary file using fully explainable and reproducible logic.

This marks the beginning of Pedro’s transition from a filesystem restructuring tool into a knowledge-driven library intelligence system.


## [0.8.0] — A Deterministic Music Library Manager Built for Safety
🚀 Pedro Organiza 0.8.0

This release solidifies Pedro’s core architecture and safety model.
It focuses on making file operations predictable, reviewable, and safe.

🔒 Deterministic Filesystem Engine
Pedro now applies file operations in a strictly deterministic way.

That means:
* The same database state always produces the same filesystem result.
* There are no hidden side effects.
* No silent modifications.
* No unexpected behavior between runs.
* Every action (move, archive, delete) is computed first and then executed in a controlled and repeatable way.

This makes Pedro predictable — especially important for large music libraries.

👀 Preview-First Architecture
Before anything touches your filesystem, you can preview exactly what will happen.

New dedicated command:
$>pedro preview

This shows:
How many files will be moved
* Archived
* Deleted (quarantined or permanently)
* Skipped

You can also limit previews:
$>pedro preview --limit 10

The apply command also supports:
$>pedro apply --dry-run

Which simulates execution without making any changes.
Nothing happens unless you explicitly tell Pedro to apply it.
Safety is the default.

Schema-Safe Database Migrations
Pedro now supports automatic, non-destructive database schema upgrades.

When new columns or features are introduced:
* Your existing database is upgraded automatically.
* No full re-scan is required.
* No data is lost.
* No manual SQL needed.

This allows Pedro to evolve over time without breaking your existing library.

🗑 Improved Deletion Safety
Deletion behavior is now explicit and guarded:

* By default, files are quarantined — not permanently deleted.
* Permanent deletion requires explicit confirmation.
* Permanent delete operation requires typing DELETE interactively.
* A lock file prevents concurrent apply operations.

Pedro assumes your music library is valuable — because it is.

🧭 CLI Structure Improvements
The CLI has been reorganized for clarity:
* pedro db namespace for database operations
* pedro analyze (alias: scan)
* pedro preview
* pedro apply
* pedro version

The help output is now cleaner and more structured.

🏗 Architectural Foundation for Future Features
0.8.0 focuses on backend integrity.
This lays the groundwork for:
* Export Profiles
* Partial exports
* Advanced filters
* UI improvements
* Safer batch operations

This release strengthens the foundation before expanding functionality.



## [0.7.0] — Structural Confidence Release

Pedro Organiza reaches an important architectural milestone with this release.  
Version 0.7.0 establishes the foundational system boundaries that will support future operational features while maintaining Pedro’s core philosophy of determinism, auditability, and user control.

This is not a feature-heavy release — it is a **stability and structure release**.

---

### Added
- Canonical CLI spine with unified entrypoint.
- `analyze` command introduced as the primary library analysis verb.
- Configuration backbone (`config.json` + config service).
- Persistent active database tracking.
- Startup inspection utilities.
- Deterministic execution layer improvements.
- Genre management command set.
- i18n-aware CLI output.

---

### Improved
- Clear separation between analysis and execution responsibilities.
- Database treated strictly as the single source of truth.
- Operator-facing command vocabulary stabilized.
- Internal schema evolution safeguards expanded.
- Overall system predictability and auditability strengthened.

---

### Design Direction
Pedro is intentionally evolving toward a professional-grade library restructuring engine built on:

- Review-before-apply workflows  
- Deterministic filesystem actions  
- Explicit operator control  
- Safe lifecycle transitions  

Future releases will focus on execution ergonomics, plan visibility, and operational tooling — not architectural rewrites.

---

### Compatibility Notes
- Legacy commands remain available where necessary but are being gradually superseded by clearer operator verbs.
- No destructive behavior is introduced in this release on purpose, but will be introduced in the future.


---

## [0.5.0] — Execution Backbone & Lifecycle Model

Version 0.5.0 introduced the early execution architecture and lifecycle concepts that transformed Pedro from an analysis tool into an operational system.

The database was elevated to authoritative status, enabling deterministic filesystem actions derived strictly from recorded state.

---

### Added
- Initial execution engine for planned filesystem operations.
- File lifecycle state tracking.
- Soft-delete model with quarantine support.
- Recommended path persistence.
- Expanded metadata support.
- Genre schema and mapping infrastructure.
- Tagging foundations for future library enrichment.

---

### Improved
- Clear separation between discovery, decision, and execution phases.
- Safer operational posture for real-world collections.
- Schema designed for additive evolution without forced rescans.

---

### Design Direction
Pedro moved decisively toward a review-before-apply workflow, prioritizing auditability and operator control over automation.

This release positioned the project as a library restructuring engine rather than a metadata utility.

---

## [0.3.0] — Normalization & Signal Foundations

This release marked Pedro’s transition from a pure ingestion tool into a system capable of reasoning about library structure.

Foundational normalization logic and duplicate-detection signals were introduced, laying the groundwork for deterministic library restructuring.

---

### Added
- Canonical text normalization pipeline.
- Normalized metadata columns for stable comparisons.
- Early duplicate-detection signals (hash + metadata).
- Alias relationship views within SQLite.
- Schema upgrade helpers for forward-compatible evolution.

---

### Improved
- Metadata consistency across ingested files.
- Database prepared for relational signal analysis.
- Internal structure moved toward deterministic outcomes rather than heuristic guesses.

---

### Design Direction
Pedro began shifting toward a database-first architecture where filesystem actions would eventually derive from structured knowledge rather than runtime inference.

This release established the analytical backbone required for safe large-library operations.

---

## [0.1.0] — Initial Release
Pedro Organiza is a tool for organizing music libraries.
- Initial CLI interface (`pedro`)
- SQLite-based knowledge ingestion
- Metadata extraction
- SHA-256 hashing
- Optional audio fingerprinting (Chromaprint)
- Album art discovery (embedded and filesystem)
- Safe, non-destructive design
- Linux, macOS, and Windows installers

This release focuses on ingestion and inspection.
Normalization and alias detection are planned.


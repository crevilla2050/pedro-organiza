# Pedro Organiza 🎵  
**A non-destructive, review-before-apply music library organizer for large, messy collections**

Pedro Organiza is a local-first music library intelligence system designed to analyze, understand, and safely reorganize large real-world music collections.

Unlike most tools, Pedro does **not** rename, delete, or modify your files by default.

Instead, it:

- Builds a complete, inspectable SQLite knowledge base  
- Detects duplicates, variants, and ambiguous metadata  
- Surfaces conflicts instead of auto-fixing them  
- Lets *you* review and explicitly decide what happens  

> **Knowledge first. Actions later. Always auditable.**

Pedro is built for people who:

- Have tens of thousands of tracks  
- Don’t trust one-click automation  
- Want full control, traceability, and reproducibility  

This is not a cleanup script.  
This is a **library intelligence system**.

---

## Why Pedro Organiza Exists

Most music tools assume:
- Small libraries
- Clean, consistent tags
- One-click automation
- Irreversible actions

Real collections rarely fit that model.

Pedro Organiza is designed for:
- Tens of thousands of tracks
- Inconsistent or conflicting metadata
- Multiple versions of the same recordings
- Long-running analysis jobs
- Users who want **control, safety, and traceability**

Pedro does not guess what you want.  
It gives you **evidence**, **structure**, and **context** so you can decide correctly.

---

## Core Principles

### Knowledge Before Action
All analysis happens first.  
Files are **never modified** during ingestion or analysis.

### Human-in-the-Loop
Ambiguities are **surfaced**, not auto-fixed.  
Pedro assists; it never overrides your judgment.

### Database as Source of Truth
All knowledge, tags, genres, clusters, decisions, plans, and states live in SQLite.  
The filesystem is an **execution target**, not a database.

### Deterministic & Auditable
You can stop, resume, inspect, revise, and replay operations safely.  
Every step is reproducible.

### Low-Resource Friendly
Designed to run on laptops, NAS boxes, home servers, and Raspberry Pi–class hardware.  
No aggressive parallelism. No hidden background jobs.

---

## High-Level Architecture

Pedro Organiza follows a **layered pipeline by design**, not convenience.

### Layer 1 — Ingest & Knowledge (Stable)
- Recursive file discovery
- Metadata extraction (audio tags)
- SHA-256 hashing
- Optional audio fingerprinting (Chromaprint)
- Album art discovery (embedded + filesystem)
- Genre ingestion and normalization
- Alias signal generation
- All results stored in SQLite

➡️ **No file mutation**

---

### Layer 2 — Analysis & Clustering (Stable)
- Duplicate detection (hash, fingerprint, metadata)
- Transitive alias clustering
- Confidence & signal aggregation
- Canonical candidate identification (advisory)

➡️ Produces **clusters**, not actions

---

### Layer 3 — Planning (In Progress)
- Human-reviewed decisions
- Tag- and genre-assisted filtering
- Planned actions stored in DB
- No implicit execution

---

### Layer 4 — Execution (Conservative by Design)
- Applies **only explicitly planned actions**
- Filesystem changes driven strictly from database state
- No irreversible deletes

---

### Layer 5 — UI (Active Development)
- React-based frontend
- Full library browsing (no pagination by design)
- Alias cluster review
- Tag & genre side panel
- Track preview (per-file)
- Future: mini player, playlist export

---

## What Pedro Can Do Today

### Backend / CLI
- Build complete SQLite knowledge databases from large libraries
- Detect duplicates and recording variants
- Normalize genres
- Generate alias clusters
- Apply soft tags (DB-only, no file mutation)
- Inspect everything safely

### API
- Read-only endpoints for:
  - Files
  - Alias clusters
  - Tags
  - Genres
  - Selection logic (applied / partial / available)
- Stable contracts for UI consumption

### UI (Prototype)
- Browse full library
- Inspect alias clusters
- Preview tracks
- Apply tags
- Filter by tags, genres, artist, cluster

---

## What Pedro Organiza Is Not

- ❌ Not a one-click “organize my music” tool  
- ❌ Not a destructive cleanup script  
- ❌ Not a tag-only fixer  
- ❌ Not a black-box automation engine  

Pedro Organiza is a **library intelligence system**, not a magic wand.

---

## Installation

Pedro Organiza is distributed as a **local CLI tool** with an optional UI.

### Requirements
- Python **3.9+**
- Read access to your music library
- Write access to the Pedro project directory
- Disk space for SQLite databases (can be large)

---

### Quick Install (Linux / macOS)

```bash
chmod +x install.sh
./install.sh

Then:

source venv/bin/activate
pedro status

### Quick Install (Windows)

install.bat

Then:

venv\Scripts\activate
pedro status

### Usage

pedro run backend/consolidate_music.py \
  --src "/path/to/music" \
  --db "my_library.sqlite" \
  --with-fingerprint \
  --search-covers \
  --progress

➡️ Builds a complete knowledge database without modifying files.

Project Structure

pedro-organiza/
├── backend/        # Core services (alias, tags, genres, planning)
├── cli/            # CLI entrypoints
├── databases/      # SQLite knowledge bases
├── music-ui/       # React frontend
├── tools/          # Inspectors & helpers
├── tests/
├── install.sh
├── install.bat
├── README.md
└── LICENSE

Current Status
* Ingestion pipeline: stable
* Alias clustering: stable
* Tags & genres: stable
* Planning & execution: in progress
* UI: active development

Pedro is best suited for users comfortable with:
* Python
* SQLite
* Inspectable systems

Roadmap Highlights
* Mini audio player (UI)
* Playlist export (M3U, XSPF, XML)
* Canonical resolution workflows
* Temporary / seasonal tags
* Action planner UI
* Execution audit trail UI

## License

Pedro Organiza is released under a Non-Commercial License.

- Free for personal and non-commercial use  
- Source available  
- Commercial use is not permitted without explicit permission  

If you wish to use Pedro Organiza in a commercial product, service, or offering,
please contact: carlos.revilla.m@gmail.com

Contributing

Pedro Organiza’s architecture is stabilizing.
Feedback and contributions are welcome, especially around:
* Duplicate resolution strategies
* Metadata normalization rules
* UX for large libraries
* Real-world edge cases

Formal contribution guidelines will follow.

Pedro Organiza is built for people who care about their music libraries
and want to understand them before changing them.
================================
Development Status (v0.3.x)

Pedro Organiza is currently in an active stabilization phase focused on making the system safe and scalable for very large real-world libraries.

As of v0.3.0, the project has reached a stable UI and API baseline on top of which execution and planning features will be built.

Key Characteristics of v0.3.0

Safe by default for large libraries
* The UI no longer loads the full file table on startup.
* Files are only fetched after explicit filtering.
* This allows Pedro to operate safely with libraries of 30k–100k+ tracks without exhausting memory or freezing the UI.

Database-first editing model
* All metadata edits are applied immediately to the SQLite database via API.
* Tag and genre edits are applied immediately to linking tables.
* The database is always the source of truth.
* No metadata or tag changes are deferred to an “Apply” phase.

Explicit execution boundary
In Pedro 1.0:
* The Apply phase does not handle metadata or tags.
* The Apply Engine will only handle:
  + Physical deletion of files marked with mark_delete = 1
  + Deletion of corresponding database rows
  + Generation of timestamped apply reports
* No moves, copies, or transcodes are performed in v1.

This strict separation ensures:
* Metadata is always reversible.
* Destructive operations are explicit, auditable, and isolated.

UI maturity
The main FileTable and bulk editing workflow are now considered structurally stable:
* Scalable selection model with visible-only bulk selection
* Compact bulk edit toolbar integrated into the native layout
* Indeterminate header checkbox for partial selections
* No legacy selection overlays
* Native dark theme fully restored
* Internationalization cleaned and consistent (mostly)

This UI baseline is intended to remain stable while execution features are added.

What Is Implemented Today
* Full ingestion pipeline to SQLite (stable)
* Alias clustering and duplicate detection (stable)
* Tag and genre management (stable)
* React UI for:
  + Filtering large libraries
  + Editing metadata
  + Applying tags
  + Previewing tracks
  + Bulk metadata edits
  + Marking files for deletion (staging only)

No filesystem mutation occurs during normal UI usage.
------
What Is Not Implemented Yet
The following are intentionally not implemented as of v0.3.x:
* Apply Engine v1 (physical deletion)
* Dry-run apply reports
* Action planner UI
* Move / copy / transcode operations
* Canonical resolution workflows

These are planned for upcoming releases and will be introduced conservatively.

Intended Audience (Current Phase)
Pedro Organiza is currently best suited for users who:
* Have large, messy music libraries
* Are comfortable with:
  + Python
  + SQLite
  + Inspecting databases directly
* Want to analyze and clean their library before executing destructive actions
* Value auditability and control over automation

Stability Note
* Database schema is considered stable for v0.3.x.
* API contracts used by the UI are now considered stable.
* UI layout protocol (pedro-fixed-header, sticky stack, scroll body) is now fixed.

Future development will focus on:
* Apply Engine v1
* Dry-run execution reports
* Execution audit trail UI
* Planning workflows


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

License

Pedro Organiza is released under the MIT License
for personal, educational, and non-commercial use.

Commercial use requires a separate license.
Contact the author for details.

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

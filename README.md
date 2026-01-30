# Pedro Organiza 🎵

**A deterministic, review-before-apply music library intelligence system**

Pedro Organiza is a **local-first music library analysis and curation system** designed for large, messy, real-world collections.

Pedro does **not** rename, delete, move, or modify your files by default.

Instead, it:

* Builds a complete, inspectable SQLite knowledge base
* Detects duplicates, variants, and ambiguous metadata
* Normalizes and curates genres safely
* Surfaces conflicts instead of auto-fixing them
* Lets **you** review and explicitly decide what happens

> **Knowledge first. Actions later. Always auditable.**

Pedro is built for people who:

* Have tens of thousands of tracks
* Don’t trust one-click automation
* Want control, traceability, and reproducibility

This is not a cleanup script.
This is a **library intelligence system**.

---

## Why Pedro Organiza Exists

Most music tools assume:

* Small libraries
* Clean tags
* One-click automation
* Irreversible actions

Real collections rarely fit that model.

Pedro Organiza is designed for:

* Tens of thousands of tracks
* Inconsistent or conflicting metadata
* Multiple recordings of the same work
* Long-running analysis jobs
* Users who value **control, safety, and evidence**

Pedro does not guess what you want.
It gives you **structure, signals, and context** so you can decide correctly.

---

## Core Principles

### Knowledge Before Action

All analysis happens first.
Files are **never modified** during ingestion or curation.

### Human-in-the-Loop

Ambiguities are **surfaced**, not auto-fixed.
Pedro assists; it never overrides your judgment.

### Database as Source of Truth

All metadata, genres, tags, clusters, and decisions live in SQLite.
The filesystem is an **execution target**, not a database.

### Deterministic & Auditable

You can stop, resume, inspect, revise, and replay operations safely.
Every result is reproducible.

### Resource-Conscious

Designed for laptops, NAS boxes, home servers, and Raspberry Pi-class hardware.
No aggressive parallelism. No background magic.

---

## High-Level Architecture

Pedro Organiza follows a **layered pipeline by design**.

### Layer 1 — Ingest & Knowledge (Stable)

* Recursive file discovery
* Metadata extraction (audio tags)
* SHA-256 hashing
* Optional audio fingerprinting (Chromaprint)
* Album art discovery (embedded + filesystem)
* **Genre ingestion, normalization, and mapping**
* Alias signal generation
* All results stored in SQLite

➡️ **No file mutation**

---

### Layer 2 — Analysis & Clustering (Stable)

* Duplicate detection (hash, fingerprint, metadata)
* Transitive alias clustering
* Signal confidence aggregation
* Canonical candidate identification (advisory only)

➡️ Produces **knowledge**, not actions

---

### Layer 3 — Planning (Active Development)

* Human-reviewed decisions
* Tag- and genre-assisted filtering
* Planned actions stored in DB
* No implicit execution

---

### Layer 4 — Execution (Intentionally Conservative)

* Applies **only explicitly planned actions**
* Filesystem changes driven strictly from database state
* No irreversible deletes without confirmation

---

### Layer 5 — UI (Active Development)

* React-based frontend
* Full library browsing (filter-first, scalable)
* Alias cluster inspection
* **Genre normalization & merging UI**
* Tag & genre side panels
* Track preview

---

## What Pedro Can Do Today (v0.5.0)

### Backend / CLI

* Scan very large music libraries into SQLite
* Perform schema-only migrations safely
* Detect duplicates and recording variants
* Generate alias clusters deterministically
* Discover, normalize, merge, and curate genres
* Inspect database state via `pedro status`
* Apply **database-only** edits (no file mutation)

### Genres (First-Class Feature)

* Canonical genre table with normalization
* Multiple raw genres mapped to one canonical genre
* Safe bulk reassignment of genres
* OR-based genre filtering
* UI + CLI aligned on the same model

### API

* Read-only and controlled-write endpoints for:

  * Files
  * Alias clusters
  * Tags
  * Genres
  * Selection states (applied / partial / available)

### UI

* Browse large libraries safely
* Filter by tags, genres, artist, cluster
* Inspect alias clusters
* Preview tracks
* Apply tags and genres
* Bulk metadata edits
* Mark files for deletion (staging only)

---

## What Pedro Organiza Is Not

* ❌ Not a one-click organizer
* ❌ Not a destructive cleanup script
* ❌ Not a black-box automation engine
* ❌ Not a tag-only fixer

Pedro Organiza is a **library intelligence system**, not a magic wand.

---

## Installation

Pedro Organiza is distributed as a **local CLI tool** with an optional UI.

### Requirements

* Python **3.9+**
* Read access to your music library
* Write access to the Pedro project directory
* Disk space for SQLite databases (can be large)

---

### Quick Install (Linux / macOS)

```bash
chmod +x install.sh
./install.sh

source venv/bin/activate
pedro status
```

### Quick Install (Windows)

```bat
install.bat
venv\Scripts\activate
pedro status
```

---

## Basic Usage

```bash
pedro db-set databases/my_library.sqlite

pedro scan \
  --src "/path/to/music" \
  --lib "/path/to/library" \
  --db-mode full
```

➡️ Builds a complete knowledge database **without modifying files**.

---

## Project Structure

```
pedro-organiza/
├── backend/        # Core analysis, genres, planning
├── cli/            # CLI entrypoints
├── databases/      # SQLite knowledge bases
├── music-ui/       # React frontend
├── tools/          # Inspectors & helpers
├── tests/
├── install.sh
├── install.bat
├── README.md
└── LICENSE
```

---

## Current Status (v0.5.0)

* Ingestion pipeline: **stable**
* Alias clustering: **stable**
* Tags & genres: **stable**
* CLI + UI alignment: **stable**
* Planning layer: **in progress**
* Execution / export: **intentionally pending**
* UI: **active development**

Pedro is best suited for users comfortable with:

* Python
* SQLite
* Inspectable systems

---

## Roadmap Highlights

* Export plan execution engine
* Dry-run execution reports
* Execution audit trail UI
* Playlist export (M3U, XSPF, XML)
* Canonical resolution workflows
* Mini audio player (UI)

---

## License

Pedro Organiza is released under a **Non-Commercial License**.

* Free for personal and non-commercial use
* Source available
* Commercial use requires explicit permission

Contact: **[carlos.revilla.m@gmail.com](mailto:carlos.revilla.m@gmail.com)**

---

## Contributing

Pedro Organiza’s architecture is stabilizing.

Feedback and contributions are welcome, especially around:

* Genre normalization rules
* Duplicate resolution strategies
* UX for very large libraries
* Real-world edge cases

Formal contribution guidelines will follow.

---


# Pedro Organiza

Pedro Organiza is a **music library curator, librarian, and organizer** designed to solve a very specific and very real problem:

Messy music libraries that have grown organically for years and are no longer manageable.

Pedro is not a media player.  
Pedro is not a streaming app.  
Pedro is not a tagger-only script.

Pedro is a **curation system**.

Its goal is to help you:
- Understand your music library
- Detect inconsistencies and duplicates
- Normalize metadata
- Organize files deterministically
- Materialize a clean, portable, future-proof music collection

Pedro is designed for **large libraries** (tens of thousands of tracks) and **deliberate, human-in-the-loop curation**.

---

## Philosophy

Pedro follows a few non-negotiable principles:

1. **Database first, filesystem last**
   - All decisions happen in a database.
   - Files are never touched until the user explicitly applies changes.

2. **Deterministic behavior**
   - No “magic guessing”.
   - No silent mutations.
   - No background auto-fixes.

3. **Human control**
   - Every important decision is visible.
   - Bulk actions are explicit.
   - Nothing is applied without confirmation.

4. **Scalability**
   - No pagination by default.
   - Designed to handle 30k+ tracks comfortably.
   - Filters, not pages.

5. **Transparency**
   - You can always see what will change before it changes.
   - Preview before commit.
   - Dry runs are first-class citizens.

---

## What Pedro IS

- A **music library curator**
- A **metadata normalization tool**
- A **duplicate detection and resolution system**
- A **preview-first editor** (listen before you decide)
- A **library organizer** that can:
  - Copy curated subsets
  - Move and consolidate libraries
  - Export playlists and trees
- A **workflow**, not a one-click tool

---

## What Pedro is NOT

- Not a streaming service
- Not a replacement for a media player
- Not a background daemon that auto-edits files
- Not designed for casual “just play music” usage
- Not destructive by default

Pedro assumes you care about your library.

---

## Architecture Overview

Pedro is composed of three main layers:

### 1. CLI (Command Line Interface)

The CLI is used to:
- Scan directories
- Populate the database
- Detect aliases and duplicates
- Generate normalization candidates
- Perform batch operations

This is where **analysis happens**, not UI.

### 2. Backend API (FastAPI + SQLite)

The API:
- Exposes the curated database
- Provides deterministic search and filtering
- Streams audio previews
- Manages tags, genres, aliases, and clusters
- Acts as the single source of truth

No UI logic lives here.

### 3. Web UI (React)

The UI:
- Is a **curation console**
- Shows filtered views of the library
- Allows editing metadata
- Supports bulk edits
- Plays previews
- Never mutates files directly

---

## Installation

### Requirements

- Python 3.10+
- Node.js 18+
- SQLite 3
- ffmpeg (recommended, for preview consistency)
- A large amount of patience and love for your music

---

### Backend Setup

1. Clone the repository

$> git clone https://github.com/your-username/pedro-organiza.git
$> cd pedro-organiza


2. Create a virtual environment
$> python -m venv venv
$> source venv/bin/activate


3. Install backend dependencies
$> pip install -r requirements.txt

4. Create a `.env` file
MUSIC_DB=/absolute/path/to/pedro.db


5. Run the API
$> uvicorn main:app --reload

The API will be available at:
http://localhost:8000

---

### Frontend Setup

1. Navigate to the UI directory
$> cd music-ui


2. Install dependencies
$> npm install


3. Start the development server
$> npm run dev

The UI will be available at:
http://localhost:5173


---

## CLI Usage (Core Commands)

Pedro’s CLI is designed to be **explicit and step-based**.
Typical workflow:

### 1. Scan music library

$> pedro scan /path/to/music

- Reads files
- Extracts basic metadata
- Populates the database
- Does NOT modify files

### 2. Detect aliases / duplicates

$> pedro aliases detect

- Finds duplicate tracks
- Groups similar files into clusters
- Does not auto-resolve

### 3. Generate normalization candidates

$> pedro normalize prepare

- Prepares canonical forms
- Suggests metadata fixes
- Leaves decisions to the user

### 4. Launch UI for curation

$> pedro ui

- Opens the web UI
- Allows manual review and editing

### 5. Apply changes (optional, explicit)

$> pedro apply

- Writes approved metadata
- Moves or copies files if configured
- Updates database paths

---

## Current UI Features

### Filtering
- Search by artist / album / title
- Alphabetical filters (A–Z, #)
- Instant backend-backed filtering
- No pagination

### Editing
- Single-row expansion for detailed editing
- Bulk editing when 2+ tracks are selected
- Dirty-state tracking per row
- Visual indicators for unsaved changes

### Playback
- Per-row audio preview
- Seek ±10 seconds
- Preview does not affect playback queue

### Safety
- No writes without explicit user action
- No hidden mutations
- Clear visual feedback

---

## Backend API Highlights

- `/files/search` — deterministic filtering
- `/files/{id}` — single-row refresh
- `/audio/{id}` — HTTP range streaming
- `/aliases/clusters` — duplicate groups
- `/side-panel/tags` — contextual tag loading
- `/side-panel/genres` — genre management

All endpoints are designed to be:
- Stateless
- Predictable
- UI-agnostic

---

## Internationalization (i18n)

Pedro supports i18n at both UI and message level.

- UI strings are key-based
- New languages can be added easily
- Backend responses are key-oriented where applicable

---

## State of Development

Pedro is **actively developed**.

Current focus:
- Solidifying search and filtering
- Bulk edit workflows
- Tag and genre side panel
- Materialization (copy / move to destination)
- Tree-based visualization
- Playlist export

Future features:
- Tree presets
- Drag-and-drop hierarchy definitions
- Export curated trees to USB / external drives
- Playlist export (M3U, etc.)
- Headless / CLI-only workflows

Pedro is already usable, but **not yet “finished”** — by design.

---

## Recent Enhancements (2026)

Pedro has recently gained a major internal upgrade that makes it safer, more flexible, and much more future-proof.

These changes are designed to eliminate forced rescans, preserve manual curation work, and unlock richer metadata workflows.

---

## Extended Metadata Support

Pedro now natively supports additional music metadata fields beyond the classic core tags:

- Composer
- Year
- BPM
- Disc #
- Disc total
- Track total
- Comment
- Lyrics
- Publisher

These fields are:

- Auto-extracted during scans
- Fully editable in the UI
- PATCH-writable via the backend API
- Tracked for dirty-state changes
- Included in both single-row and bulk updates

This makes Pedro suitable not only for pop/rock libraries but also for:

- Classical collections
- Soundtracks
- Jazz archives
- Audiobook libraries
- DJ-style BPM-driven libraries

---

## Auto-Migrating Database Schema

Pedro now performs **safe, additive schema upgrades** on startup.

When new metadata columns are introduced:

- The backend automatically checks the existing database schema
- Missing columns are added using idempotent migrations
- No data is destroyed
- No rescan is required
- No user action is required

This guarantees:

- Forward compatibility between Pedro versions
- Zero-loss upgrades
- No forced library re-indexing

In other words:  
You can upgrade Pedro without paying the price of re-scanning 30,000+ tracks again.

---

## Controlled Database Update Modes

Pedro’s CLI now supports multiple update strategies to protect manual edits and reduce unnecessary work:

--db-mode full  
  Full scan. Refreshes metadata, fingerprints, and recommendations.

--db-mode tags-only  
  Only refreshes tag metadata from files.  
  Does NOT recompute fingerprints or paths.

--db-mode normalize-only  
  Only recomputes normalized text fields used for alias detection.

--db-mode schema-only  
  Only applies schema migrations.  
  Does NOT scan files at all.

--db-mode no-overwrite  
  Updates only missing fields.  
  Never overwrites existing user-edited metadata.

These modes allow you to:

- Safely refresh manually edited tags
- Add new metadata fields retroactively
- Avoid redoing heavy work like fingerprinting
- Evolve your library schema without downtime

---

## Single + Bulk Metadata Editing (UI)

Pedro’s UI now supports:

- Per-row inline editing
- Dirty-state tracking (visual + structural)
- Per-row Apply buttons
- Multi-row bulk edits
- Backend-backed PATCH persistence

Key behaviors:

- Rows become visually marked when modified
- Unsaved edits are never applied automatically
- Dirty rows show:
  - A left-side highlight bar
  - A visible star indicator (*)
- Bulk edits are only enabled when 2+ rows are selected
- All updates go through deterministic backend APIs
- Local UI state is refreshed only after successful server writes

This preserves Pedro’s core philosophy:

No silent changes.  
No accidental data loss.  
No magical background saves.

---

## New Backend Endpoints

The backend API has been extended to support safe write operations:

PATCH /files/{id}  
  Update metadata fields for a single file.

PATCH /files/bulk  
  Apply the same metadata updates to multiple files.

Both endpoints:

- Accept partial field updates
- Only modify explicitly provided fields
- Return updated row payloads
- Never mutate filesystem contents

This cleanly separates:

Database curation  
from  
Filesystem materialization

---

## Internationalization Discipline

Pedro now follows strict i18n discipline across the UI:

- All user-facing strings are key-based
- Language dictionaries live in /music-ui/src/i18n
- New UI strings must be registered in:
  - en.js
  - es.js
  - de.js
- Backend responses are also key-oriented where applicable

This guarantees:

- No hardcoded UI strings
- No future translation debt
- A clear path to multi-language support

---

## Forward Direction: Startup / First-Run UI (Planned)

Pedro is transitioning away from a CLI-first onboarding experience.

A new **Startup / First-Run UI** is planned to allow non-technical users to:

- Choose a source music directory
- Choose a target library directory
- Design folder structure visually (drag-and-drop)
- Configure scan options
- Launch the initial scan from the UI
- Track scan progress live
- Enter the main Pedro UI after completion

This will remove the need to:

- Manually run CLI commands
- Hand-edit .env files
- Understand backend bootstrapping

CLI will remain available for power users,  
but UI will become the primary onboarding path.

---

## Compatibility Promise

Pedro makes the following stability guarantees:

- New versions will never silently destroy existing DB data
- Schema upgrades will always be additive
- Manual UI edits will never be overwritten unless explicitly requested
- Files will never be touched without explicit user confirmation
- No feature will require forced re-scans unless strictly unavoidable

---

## Development Status (Updated)

Pedro is now beyond the "prototype" stage.

Current stability tier:
- Backend: Stable core
- Database: Forward-compatible
- UI: Feature-complete for core workflows

Active development focus:
- Startup / First-run UI
- Library materialization (copy/move executor)
- Tree presets and layout builder
- Playlist export
- Alias cluster resolution workflows
- Visual tree preview
- Review-before-apply pipeline

Pedro is not a toy.  
Pedro is not a weekend script.

Pedro is becoming a serious long-term library curation system.

---

## Final Note

Pedro Organiza is evolving from:

"A script I use to clean my library"

into:

"A deterministic, review-first, future-proof music curation platform"

If you care about your music library,  
Pedro will respect that.

If you don’t,  
there are easier tools 🙂

---

## Contributing

Pedro was born out of a personal need, but contributions are welcome.

If you contribute:
- Respect the philosophy
- Avoid hidden automation
- Keep behavior deterministic
- Document everything

---

## License

TBD (planned: permissive open-source license)

---

## Final Words

Pedro Organiza exists because messy music libraries are a solved problem **only if you care**.

If you don’t care, there are easier tools.

If you do care — Pedro is for you.


---

## Contact

For questions, feedback, or contributions:

- Open an issue on GitHub
- Email: carlos.revilla.m@gmail.com (TBD)

---

## End of Document
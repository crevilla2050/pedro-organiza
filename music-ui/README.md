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

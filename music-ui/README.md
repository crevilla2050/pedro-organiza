# Pedro Organiza 🎵

Pedro Organiza is a **music library librarian**, not a player-first app.

It is designed to **analyze, clean, normalize, and reorganize large and messy music collections** with surgical precision, while remaining transparent, deterministic, and user-controlled at every step.

Pedro does **not** try to replace your music player.  
Pedro prepares your library so *any* player can use it properly.

---

## Core Philosophy

- 🧠 **Librarian, not DJ**  
  Metadata correctness and structure come before playback.

- 🔍 **Filter-driven workflow**  
  Nothing loads until the user asks for it.  
  Large libraries (30k+ files) remain fast and usable.

- 🧱 **Deterministic backend**  
  No hidden heuristics. No magic. No silent mutations.

- 🪟 **UI reflects data reality**  
  What you see is what is in the database — always.

- 🌍 **i18n-first mindset**  
  All UI and CLI strings are designed to be translatable.

---

## Current Features (UI)

- File table with:
  - Inline editable metadata
  - Expandable rows for secondary tags
  - Bulk edit panel (context-aware)
  - Per-row audio preview with ±10s seek
- Always-visible filter bar with:
  - Single flexible search field
  - Search scope selector (Artist / Album / Title)
  - Alphabetic filtering (A–Z / #)
  - Clear filters behavior that **does not auto-load everything**
- Side panel:
  - Collapsible / movable (left or right)
  - Mini-player mock (future global playback)
- Designed to handle **35k+ tracks** without pagination

---

## Backend Highlights

- FastAPI + SQLite
- Explicit API contracts
- No filesystem mutation in preview phase
- Audio streaming with proper HTTP range support
- Deterministic search API:
  - Flexible vs strict matching
  - Case-insensitive by default
  - Optional wildcard support (`*`, `?`)
  - Server-side sorting
  - No pagination by design

---

## Important Design Decisions

- ❌ No automatic full library load  
  Users must refine searches before results appear.

- ❌ No pagination  
  Filtering is preferred over slicing data.

- ✅ Backend-first scalability  
  UI is wired to explicit search endpoints, not raw tables.

- ✅ Future-proof architecture  
  Designed for:
  - Tree-based views (Artist → Album → Track)
  - Playlist export (M3U, etc.)
  - User-defined tree presets
  - Incremental “apply to disk” workflows

---

## What Pedro Is *Not*

- ❌ A replacement for your music player
- ❌ A black-box tagger
- ❌ An opinionated “one-click” organizer

Pedro is a **workbench**, not a button.

---

## Status

🚧 **Active development**

Current focus:
- Filter-driven search UX
- Backend search correctness
- i18n compliance
- Preparing groundwork for tree views and materialization

---

## License

TBD (will be decided before first public release)

---

## Author

Pedro Organiza is built by someone who got tired of messy libraries —  
and decided to fix the problem *properly*.

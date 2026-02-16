# Pedro Organiza

**Deterministic music library management for people who care about their collections.**

Pedro is a database‑first music library restructuring engine designed for safety, reproducibility, and large real‑world collections.

Unlike traditional organizers that mutate files directly, Pedro builds a structured knowledge base first and lets you review every decision before anything touches your filesystem.

---

# Project Philosophy

Pedro is built on a few non‑negotiable ideas.

## 1. Your music is valuable

Music libraries are often:
- Decades old
- Irreplaceable
- Full of rare files
- Emotionally meaningful

Pedro assumes your collection matters.

That means:
- No silent mutations
- No hidden automation
- No destructive defaults

---

## 2. Database first, filesystem second

Most organizers operate like this:

Scan → Mutate files → Hope for the best

Pedro does the opposite:

Scan → Build knowledge → Preview → Apply

The database is the source of truth.
The filesystem becomes a projection of structured knowledge.

This enables:
- Deterministic results
- Auditable decisions
- Reversible workflows

---

## 3. Determinism over “AI magic”

Pedro avoids opaque heuristics.

If the same database state exists, Pedro will always:
- Produce the same preview
- Generate the same filesystem actions
- Suggest the same duplicate decisions

No randomness.
No hidden scoring models.
No surprises.

---

## 4. Preview before execution

Nothing touches your files until you explicitly say so.

You can always:
- Preview actions
- Simulate execution
- Inspect duplicates
- Validate schema state

Safety is the default, not an option.

---

## 5. Advisory intelligence, not automation

Pedro can suggest things (like duplicate primaries), but it will never override the operator.

You remain in control.

Always.

---

# What Pedro Is (and Is Not)

## Pedro IS

- A deterministic library restructuring engine
- A knowledge graph for your music
- A safe large‑collection organizer
- A foundation for future UI tooling

## Pedro is NOT

- A media player
- A tagger replacement (though it can enrich metadata)
- An AI auto‑organizer
- A "one‑click fix everything" tool

Pedro is for people who want **control and safety**, not convenience at any cost.

---

# Requirements

Pedro runs anywhere Python runs.

## Minimum requirements

- Python 3.10+
- SQLite (bundled with Python)

## Optional (recommended)

- Chromaprint / fpcalc (for audio fingerprinting)
- Large SSD for big libraries

---

# Installation

## 1. Install Python

### Linux
Most distributions already include Python 3.

Check:

```bash
python3 --version
```

If needed:

```bash
sudo apt install python3 python3-venv python3-pip
```

---

### macOS

```bash
brew install python
```

---

### Windows

Download from:
https://www.python.org/downloads/

Make sure to check:

✔ Add Python to PATH

---

## 2. Clone Pedro

```bash
git clone https://github.com/YOUR_USERNAME/pedro-organiza.git
cd pedro-organiza
```
🚀 One-Command Install (Recommended)
Linux / macOS

```bash
chmod +x install.sh
./install.sh
```

Windows

Double-click install.bat
or run in PowerShell:

```powershell
install.bat
```

What the installer does

The installer will:
* Verify Python 3.9+
* Create a virtual environment (venv)
* Install Pedro and dependencies
* Run sanity checks
* Warn about optional tools (ffmpeg, Node.js)

No system-wide Python changes are made.

---


## 3. Create virtual environment (recommended)
Manual Installation (Advanced Users)

If you prefer manual setup:

```bash
python3 -m venv venv
pip install -U pip setuptools wheel
pip install -e .
source venv/bin/activate   # Linux/macOS
venv\Scripts\activate     # Windows
```

---

## 4. Install dependencies

```bash
pip install -r requirements.txt
pip install -e .
```

The editable install exposes the `pedro` CLI.

Verify:

```bash
pedro version
```

---

# First Run (Step‑by‑Step)

This is the safest way to start using Pedro.

## Step 1 — Create a database

Pedro works against a SQLite database.

```bash
pedro db set music.sqlite
pedro migrate
```

This initializes the schema.

Verify:

```bash
pedro status
```

You should see something like:

```
Pedro database detected OK and is ready to use.
files: 0
```

---

## Step 2 — Analyze your library

This scans files and builds knowledge without changing anything.

```bash
pedro analyze \
  --src "/path/to/your/music" \
  --lib "/path/to/canonical/library"
```

What this does:

- Extracts metadata
- Computes hashes
- Detects duplicates
- Plans filesystem actions

Nothing is modified yet.

---

## Optional flags

### Enable fingerprinting

```bash
--with-fingerprint
```

Improves duplicate detection.

---

### Search album art

```bash
--search-covers
```

Enables cover discovery pipeline.

---

# Inspecting Results

## Check database health

```bash
pedro status
```

---

## Preview filesystem actions

```bash
pedro preview
```

Shows:
- Planned moves
- Archives
- Deletes (quarantine)

---

## Simulate execution

```bash
pedro apply --dry-run
```

This performs a full simulation.

---

# Duplicate Analysis

Pedro provides deterministic duplicate clustering.

## Cluster statistics

```bash
pedro dupes stats
```

---

## Inspect largest clusters

```bash
pedro dupes largest --top 10
```

---

## Suggest a primary file

You can pass either a cluster ID or a file ID.

```bash
pedro dupes suggest 84
```

Pedro returns a transparent ranking explaining the choice.

---

## Custom suggestion policies

Prefer smaller files (for portable players):

```bash
pedro dupes suggest 84 --prefer-smallest
```

Prefer lossy formats:

```bash
pedro dupes suggest 84 --prefer-lossy
```

Prefer specific containers:

```bash
pedro dupes suggest 84 --prefer-container mp3,aac
```

All suggestions are advisory only.

Pedro never auto‑deletes duplicates.

---

# Applying Changes

When you're ready:

```bash
pedro apply
```

Default behavior:
- Moves files deterministically
- Quarantines deletions

---

## Permanent deletion (explicit opt‑in)

```bash
pedro apply --delete-permanent --yes-i-know-what-im-doing
```

Pedro requires explicit confirmation by design.

---

# Updating Schema

When Pedro evolves:

```bash
pedro migrate
```

Migrations are:
- Additive
- Non‑destructive
- Deterministic

No rescans required in most cases.

---

# Typical Workflow

```bash
pedro db set music.sqlite
pedro migrate
pedro analyze --src ~/Downloads --lib ~/Music --with-fingerprint
pedro preview
pedro dupes stats
pedro dupes suggest 1234
pedro apply --dry-run
pedro apply
```

---

# Safety Model

Pedro is intentionally conservative.

- Quarantine over deletion
- Preview before apply
- Deterministic migrations
- Explicit destructive flags

You are always in control of the final step.

---

# Roadmap (Short)

Planned directions:

- Interactive normalization workflows
- UI layer on top of the deterministic engine
- Safer batch deduplication tooling
- Export profiles and library slicing

Pedro evolves carefully to preserve trust and data safety.

---

# Contributing

Pedro is a long‑term systems project.

Contributions are welcome, especially in:

- Deterministic algorithms
- Large library testing
- Cross‑platform robustness
- Documentation clarity

---

# Final Words

Pedro exists because music libraries deserve better tools.

If you care about your collection, you deserve:
- Safety
- Transparency
- Reproducibility

Pedro is built for that.


#!/usr/bin/env python3
"""
consolidate_music.py

High-level overview
-------------------
This module implements the "knowledge" layer of a music consolidation
pipeline. Its goal is to scan a source music tree, extract metadata and
content fingerprints, compute stable file identifiers (SHA-256), suggest a
canonical destination path in the user's music library, and stage the
resulting operations in a lightweight SQLite database.

The database acts as a staging area that separates *analysis* from
*execution* — the `files` table records discovered files and metadata,
the `album_art` table stores discovered artwork candidates, and the
`actions` table records explicit intents (for example: move this file
from A to B). This two-step design (analyze -> apply) gives users an
opportunity to review and modify proposed actions before they are
actually performed.

Main responsibilities in this file:
- Discover audio files under a source directory
- Extract tags/metadata using Mutagen
- Compute SHA-256 digests for exact de-duplication
- Optionally compute audio fingerprints (Chromaprint) for fuzzy
    duplicate detection
- Suggest a sanitized, canonical path inside the user library
- Persist metadata, signals and proposed actions into a SQLite DB

This file is intentionally written as a set of small, testable
functions (utility helpers, DB helpers, metadata ingestion and the
top-level `analyze_files`). Other parts of the project are expected to
consume the DB created/updated by this module.
"""

import os
import sqlite3
import hashlib
import subprocess
import re
import unicodedata
import logging
from datetime import datetime, timezone
from pathlib import Path

from mutagen import File as MutagenFile
from dotenv import load_dotenv
from normalization import normalize_text


try:
    from tqdm import tqdm
except Exception:
    tqdm = None

try:
    import chromaprint
except Exception:
    chromaprint = None

# ================= I18N MESSAGE KEYS =================

MSG_DB_NOT_PROVIDED = "DB_NOT_PROVIDED"
MSG_LIB_NOT_PROVIDED = "LIB_NOT_PROVIDED"
MSG_FOUND_AUDIO_FILES = "FOUND_AUDIO_FILES"
MSG_ANALYSIS_COMPLETE = "ANALYSIS_COMPLETE"
MSG_SCHEMA_UPGRADE_ADD_COLUMN = "SCHEMA_UPGRADE_ADD_COLUMN"
MSG_LAUNCH_GENRE_NORMALIZATION = "LAUNCH_GENRE_NORMALIZATION"
MSG_GENRE_NORMALIZATION_FAILED = "GENRE_NORMALIZATION_FAILED"

# ================= CONFIG =================

SUPPORTED_EXTS = {".mp3", ".flac", ".wav", ".m4a", ".ogg", ".aac", ".opus"}
IMAGE_EXTS = {".jpg", ".jpeg", ".png"}
COMMON_COVER_NAMES = {"cover", "folder", "front", "album", "albumart"}

ENABLE_CHROMAPRINT = True
FP_SECONDS = 90
DATABASES_DIR = Path("databases")

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s: %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S%z",
)

# ================= ENV HELPERS =================

def _update_env(key, value):
    """
    Persist a single key=value pair into a local `.env` file.

    Behavior:
    - If `.env` exists, load existing lines and drop any previous
      occurrences of `key`.
    - Append the new `key=value` pair and write the file back.

    Note: this is a convenience helper to make CLI usage remember the
    chosen DB/library paths between runs. It is intentionally simple —
    not a replacement for a full configuration management solution.
    """

    lines = []
    if os.path.exists(".env"):
        with open(".env", "r") as f:
            lines = f.readlines()

    # Remove any existing line that sets this key, then append the
    # new one. Writing the whole file is simpler and avoids partial
    # update complexity.
    lines = [l for l in lines if not l.startswith(f"{key}=")]
    lines.append(f"{key}={value}\n")

    with open(".env", "w") as f:
        f.writelines(lines)


def resolve_env_path(key, cli_value=None):
    """
    Resolve a path from environment or CLI and persist to `.env`.

    If a `cli_value` is provided we convert it to an absolute path,
    update `.env` so future runs remember it, and return the absolute
    path. Otherwise we look for the environment variable `key`. If
    neither is present a RuntimeError is raised with a message key
    that higher-level code can interpret for i18n or user feedback.
    """

    load_dotenv(override=False)

    if cli_value:
        value = os.path.abspath(cli_value)
        _update_env(key, value)
        return value

    value = os.getenv(key)
    if value:
        return os.path.abspath(value)

    # Raise a structured error so callers can map to localized
    # messages (see MSG_* constants above).
    raise RuntimeError({
        "key": MSG_DB_NOT_PROVIDED if key == "MUSIC_DB" else MSG_LIB_NOT_PROVIDED,
        "params": {"key": key}
    })


def resolve_database_path(cli_value=None):
    """
    Resolve the SQLite database path and ensure it lives inside the
    repository `databases/` folder when a relative path is provided.

    Behavior details:
    - Create the `databases/` directory if it does not exist.
    - Prefer `cli_value` over the `MUSIC_DB` environment variable.
    - If a relative path (parent == '.') is provided we place the
      DB file under `databases/` to keep runtime artifacts together.
    - Persist the resolved absolute path back into `.env` so future
      CLI invocations use the same DB.
    """

    DATABASES_DIR.mkdir(exist_ok=True)
    load_dotenv(override=False)

    raw = cli_value or os.getenv("MUSIC_DB")
    if not raw:
        raise RuntimeError({
            "key": MSG_DB_NOT_PROVIDED,
            "params": {"key": "MUSIC_DB"}
        })

    p = Path(raw)
    # If user provided a bare filename, store it under the
    # `databases/` directory to avoid littering the working directory.
    if p.parent == Path("."):
        p = DATABASES_DIR / p

    p = p.resolve()
    _update_env("MUSIC_DB", str(p))
    return str(p)

# ================= UTILITIES =================

def log(msg):
    logging.info(msg)


def maybe_progress(it, desc=None, enable=False):
    """
    Wrap an iterator with `tqdm` progress UI only when requested and
    `tqdm` is available. This helper keeps callers free of UI
    conditional logic and makes progress optional (useful for tests
    and CI runs where a progress bar is undesirable).
    """

    if enable and tqdm:
        return tqdm(it, desc=desc)
    return it


def utcnow():
    return datetime.now(timezone.utc).isoformat()


def is_audio_file(p: Path):
    """Return True when `p` points to an audio file we can analyze.

    The function checks both that the path is a file and that the file
    extension is in the supported list. The extension check is used as
    a fast filter; Mutagen will do the final parsing during tag
    extraction.
    """

    return p.is_file() and p.suffix.lower() in SUPPORTED_EXTS


def sha256_file(path: Path):
    """Compute a streaming SHA-256 hex digest for `path`.

    Reading in 64KB chunks avoids allocating huge buffers for large
    files and keeps memory usage predictable.
    """

    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def normalize_str(s):
    """Normalize a text value by removing Unicode combining marks.

    This converts characters into NFKD form and strips diacritics so
    subsequent normalization and comparison steps are more stable.
    Returns an empty string when input is falsy.
    """

    if not s:
        return ""
    s = unicodedata.normalize("NFKD", s)
    return "".join(c for c in s if not unicodedata.combining(c)).strip()


def sanitize_for_fs(s):
    """Make a metadata string safe for use as a filename or directory.

    This helper:
    - Normalizes Unicode (removes combining marks)
    - Replaces characters invalid in filenames with underscore
    - Trims trailing spaces and dots (common filesystem nuisance)
    - Truncates to a conservative length (120 chars)

    If the input is falsy we return the literal "Unknown" so callers
    downstream can still build a path.
    """

    if not s:
        return "Unknown"
    s = normalize_str(s)
    s = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", s)
    return s.strip(" .")[:120]


def normalize_track(track_raw):
    """Normalize various `tracknumber` tag formats to a two-digit
    string like '01'.

    Typical tag values may be integers, strings like '1' or '1/12', or
    lists (depending on the tag library). This helper extracts the
    leading number and returns it zero-padded to two digits, or `None`
    when the value is not a pure digit.
    """

    if not track_raw:
        return None
    if isinstance(track_raw, list):
        track_raw = track_raw[0]
    track_raw = str(track_raw).strip()
    if "/" in track_raw:
        track_raw = track_raw.split("/", 1)[0]
    return f"{int(track_raw):02d}" if track_raw.isdigit() else None


def recommended_path_for(root, meta, ext):
    """Suggest a canonical filesystem path for a file given metadata.

    The strategy is straightforward: use `album_artist` (fall back to
    `artist`) and `album` as directory names, and a filename that
    optionally prefixes the title with a zero-padded track number.
    Filenames and directories are sanitized using `sanitize_for_fs` to
    minimise filesystem errors across platforms.
    """

    artist = sanitize_for_fs(meta.get("album_artist") or meta.get("artist") or "Unknown Artist")
    album = sanitize_for_fs(meta.get("album") or "Unknown Album")
    title = sanitize_for_fs(meta.get("title") or meta.get("orig_name"))
    track = meta.get("track")
    fname = f"{track} - {title}{ext}" if track else f"{title}{ext}"
    return str(Path(root) / artist / album / fname)


def hash_image_bytes(data: bytes) -> str:
    """Return SHA-256 hex digest for image bytes.

    Used to detect identical album art blobs coming from different
    sources (embedded artwork vs local cover files vs web-scraped
    images).
    """

    return hashlib.sha256(data).hexdigest()

# ================= DATABASE HELPERS =================

def ensure_column(c, table, column, ddl):
    """Add a column to `table` when it does not exist.

    This performs a safe, minimal schema migration by checking the
    existing columns via `PRAGMA table_info`. It is intentionally
    permissive: if the column exists nothing happens, which means this
    function is idempotent and safe to call on every startup.
    """

    cols = [r["name"] for r in c.execute(f"PRAGMA table_info({table})")]
    if column not in cols:
        log({
            "key": MSG_SCHEMA_UPGRADE_ADD_COLUMN,
            "params": {"table": table, "column": column}
        })
        c.execute(f"ALTER TABLE {table} ADD COLUMN {ddl}")


def ensure_normalized_columns(c):
    ensure_column(c, "files", "artist_norm", "artist_norm TEXT")
    ensure_column(c, "files", "album_artist_norm", "album_artist_norm TEXT")
    ensure_column(c, "files", "album_norm", "album_norm TEXT")
    ensure_column(c, "files", "title_norm", "title_norm TEXT")


def ensure_alias_views(c):
    # --- Signal A: SHA-256 ---
    c.execute("""
        CREATE VIEW IF NOT EXISTS alias_pairs_sha256 AS
        SELECT
            f1.id AS file_id,
            f2.id AS other_file_id,
            'sha256' AS signal_type,
            1.0 AS strength
        FROM files f1
        JOIN files f2
          ON f1.sha256 = f2.sha256
         AND f1.id < f2.id
        WHERE f1.sha256 IS NOT NULL
    """)

    # --- Signal B: Fingerprint ---
    c.execute("""
        CREATE VIEW IF NOT EXISTS alias_pairs_fingerprint AS
        SELECT
            f1.id AS file_id,
            f2.id AS other_file_id,
            'fingerprint' AS signal_type,
            0.9 AS strength
        FROM files f1
        JOIN files f2
          ON f1.fingerprint = f2.fingerprint
         AND f1.id < f2.id
        WHERE f1.fingerprint IS NOT NULL
    """)

    # --- Signal C: Artist + Title ---
    c.execute("""
        CREATE VIEW IF NOT EXISTS alias_pairs_artist_title AS
        SELECT
            f1.id AS file_id,
            f2.id AS other_file_id,
            'artist_title' AS signal_type,
            0.6 AS strength
        FROM files f1
        JOIN files f2
          ON f1.artist_norm = f2.artist_norm
         AND f1.title_norm = f2.title_norm
         AND f1.id < f2.id
        WHERE f1.artist_norm != ''
          AND f1.title_norm != ''
    """)

    # --- Signal D: Album + Title ---
    c.execute("""
        CREATE VIEW IF NOT EXISTS alias_pairs_album_title AS
        SELECT
            f1.id AS file_id,
            f2.id AS other_file_id,
            'album_title' AS signal_type,
            0.4 AS strength
        FROM files f1
        JOIN files f2
          ON f1.album_norm = f2.album_norm
         AND f1.title_norm = f2.title_norm
         AND f1.id < f2.id
        WHERE f1.album_norm != ''
          AND f1.title_norm != ''
    """)

    # --- Union of all signals ---
    c.execute("""
        CREATE VIEW IF NOT EXISTS alias_pairs_all AS
        SELECT * FROM alias_pairs_sha256
        UNION ALL
        SELECT * FROM alias_pairs_fingerprint
        UNION ALL
        SELECT * FROM alias_pairs_artist_title
        UNION ALL
        SELECT * FROM alias_pairs_album_title
    """)

    # --- Converged confidence ---
    c.execute("""
        CREATE VIEW IF NOT EXISTS alias_pair_confidence AS
        SELECT
            file_id,
            other_file_id,
            COUNT(*) AS signal_count,
            SUM(strength) AS confidence_score
        FROM alias_pairs_all
        GROUP BY file_id, other_file_id
    """)

    # --- Strong edges (used by cluster explorer) ---
    c.execute("""
        CREATE VIEW IF NOT EXISTS alias_strong_edges AS
        SELECT
            file_id,
            other_file_id,
            signal_count,
            confidence_score
        FROM alias_pair_confidence
        WHERE signal_count >= 2
           OR confidence_score >= 1.5
    """)

    # --- Strong edges WITH signal types (for analysis) ---
    c.execute("""
        CREATE VIEW IF NOT EXISTS alias_edges_with_signals AS
        SELECT
            p.file_id,
            p.other_file_id,
            p.signal_type,
            p.strength
        FROM alias_pairs_all p
        JOIN alias_strong_edges s
          ON (
               (p.file_id = s.file_id AND p.other_file_id = s.other_file_id)
            OR (p.file_id = s.other_file_id AND p.other_file_id = s.file_id)
          );
    """)
   

def normalize_file_row(c, file_id):
    """Compute and persist normalized textual fields for a file.

    The `normalize_text` function (imported from `normalization`) is
    the project's canonical normalizer for comparing artists,
    albums and titles. Normalized fields are used by the database
    views in `ensure_alias_views` to detect likely duplicates where
    tags differ by punctuation, case or similar noise.
    """

    row = c.execute(
        """
        SELECT artist, album_artist, album, title
        FROM files
        WHERE id = ?
        """,
        (file_id,),
    ).fetchone()

    if not row:
        return

    c.execute(
        """
        UPDATE files
        SET
            artist_norm = ?,
            album_artist_norm = ?,
            album_norm = ?,
            title_norm = ?
        WHERE id = ?
        """,
        (
            normalize_text(row["artist"]),
            normalize_text(row["album_artist"]),
            normalize_text(row["album"]),
            normalize_text(row["title"]),
            file_id,
        ),
    )


# ================= DATABASE =================

def create_db(db_path):
    """Create the SQLite schema used by the consolidation pipeline.

    The schema is intentionally minimal and focused on the needs of
    the analysis stage. Important tables:
    - `files`: discovered audio files and their extracted metadata
    - `album_art`: candidate artwork for albums
    - `actions`: explicit intents such as move/copy operations
    - `genres`, `genre_mappings`, `file_genres`: lightweight genre
      normalization and mapping support

    This function is safe to call repeatedly; `CREATE TABLE IF NOT
    EXISTS` and idempotent migrations (see `ensure_column`) allow
    incremental upgrades without complex migration tooling.
    """

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    c.executescript("""
    PRAGMA foreign_keys = ON;

    CREATE TABLE IF NOT EXISTS files (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        original_path TEXT UNIQUE,
        sha256 TEXT,
        size_bytes INTEGER,
        artist TEXT,
        album_artist TEXT,
        album TEXT,
        title TEXT,
        track TEXT,
        genre TEXT,
        duration REAL,
        bitrate INTEGER,
        fingerprint TEXT,
        is_compilation INTEGER DEFAULT 0,
        recommended_path TEXT,
        lifecycle_state TEXT DEFAULT 'new',
        first_seen TEXT,
        last_update TEXT,
        notes TEXT
    );

    CREATE TABLE IF NOT EXISTS album_art (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        album_artist TEXT,
        album TEXT,
        is_compilation INTEGER DEFAULT 0,
        image_hash TEXT,
        source TEXT,
        confidence REAL,
        mime TEXT,
        width INTEGER,
        height INTEGER,
        created_at TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS actions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        file_id INTEGER NOT NULL,
        action TEXT NOT NULL,
        src_path TEXT NOT NULL,
        dst_path TEXT,
        status TEXT DEFAULT 'pending',
        error TEXT,
        created_at TEXT NOT NULL,
        applied_at TEXT,
        FOREIGN KEY(file_id) REFERENCES files(id)
    );

    CREATE TABLE IF NOT EXISTS genres (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        normalized_name TEXT NOT NULL UNIQUE,
        source TEXT DEFAULT 'user',
        created_at TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS genre_mappings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        raw_token TEXT NOT NULL,
        normalized_token TEXT NOT NULL UNIQUE,
        genre_id INTEGER,
        source TEXT DEFAULT 'user',
        created_at TEXT NOT NULL,
        FOREIGN KEY (genre_id) REFERENCES genres(id)
    );

    CREATE TABLE IF NOT EXISTS file_genres (
        file_id INTEGER NOT NULL,
        genre_id INTEGER NOT NULL,
        source TEXT DEFAULT 'tag',
        confidence REAL DEFAULT 1.0,
        created_at TEXT NOT NULL,
        PRIMARY KEY (file_id, genre_id),
        FOREIGN KEY (file_id) REFERENCES files(id),
        FOREIGN KEY (genre_id) REFERENCES genres(id)
    );

    CREATE INDEX IF NOT EXISTS idx_genres_norm ON genres(normalized_name);
    CREATE INDEX IF NOT EXISTS idx_file_genres_file ON file_genres(file_id);
    CREATE INDEX IF NOT EXISTS idx_file_genres_genre ON file_genres(genre_id);
    CREATE INDEX IF NOT EXISTS idx_genre_mappings_norm ON genre_mappings(normalized_token);
    """)

    ensure_normalized_columns(c)
    ensure_alias_views(c)

    conn.commit()
    return conn

# ================= FINGERPRINT =================

def compute_fingerprint(path: Path):
    """Compute an audio fingerprint using Chromaprint/ffmpeg.

    Steps:
    1. Use `ffmpeg` to render the first `FP_SECONDS` seconds of audio to
       a raw PCM stream (`s16le`, mono, 44.1kHz).
    2. Feed the raw PCM to Chromaprint's fingerprinter and obtain a
       fingerprint string.
    3. Hash the fingerprint with SHA-1 to keep stored values concise
       and consistent.

    The function is defensive: when missing dependencies (`chromaprint`
    package or `ENABLE_CHROMAPRINT` disabled) or when `ffmpeg` fails
    the function returns `None` so the rest of the pipeline can still
    proceed using other signals (like SHA-256).
    """

    if not ENABLE_CHROMAPRINT or chromaprint is None:
        return None

    try:
        cmd = [
            "ffmpeg", "-v", "quiet",
            "-t", str(FP_SECONDS),
            "-i", str(path),
            "-f", "s16le",
            "-ac", "1",
            "-ar", "44100",
            "-"
        ]

        proc = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            check=True
        )

        if not proc.stdout:
            return None

        fp = chromaprint.Fingerprinter(44100, 1)
        fp.feed(proc.stdout)
        fingerprint, _ = fp.finish()

        # Store a short, stable representation by hashing the
        # fingerprint payload. SHA-1 is used here because we don't need
        # cryptographic strength — only a compact, stable id.
        return hashlib.sha1(fingerprint.encode()).hexdigest()

    except Exception:
        # Fingerprint computation is best-effort; failures shouldn't
        # abort the entire analysis pipeline.
        return None
    
# ================= METADATA =================

def extract_tags(path: Path):
    """Extract tags and technical info from an audio file using
    Mutagen.

    The function returns a dictionary with the canonical keys used by
    the rest of the pipeline. It is defensive: when Mutagen cannot
    parse the file or a particular tag is missing we return `None`
    values, and we also include `orig_name` (the file stem) so files
    without tags still get a usable suggested filename.

    The `is_compilation` flag is detected by looking for common tag
    frames used by different formats (TCMP, CPIL, etc.). We check the
    raw tag container (`easy=False`) to find these signals.
    """

    try:
        audio = MutagenFile(path, easy=True)
        raw = MutagenFile(path, easy=False)

        album_artist = audio.get("albumartist", [None])[0] if audio else None
        is_comp = 0

        # Some formats expose a dedicated compilation flag — check the
        # low-level tag container keys to detect it reliably.
        if raw and hasattr(raw, "tags"):
            for k in raw.tags.keys():
                if str(k).lower() in ("tcmp", "compilation", "cpil"):
                    is_comp = 1
                    break

        return {
            "artist": audio.get("artist", [None])[0] if audio else None,
            "album_artist": album_artist,
            "album": audio.get("album", [None])[0] if audio else None,
            "title": audio.get("title", [None])[0] if audio else None,
            "track": normalize_track(audio.get("tracknumber", [None])[0]) if audio else None,
            "genre": audio.get("genre", [None])[0] if audio else None,
            "duration": getattr(audio.info, "length", None) if audio else None,
            "bitrate": getattr(audio.info, "bitrate", None) if audio else None,
            "is_compilation": is_comp,
            "orig_name": path.stem,
        }
    except Exception:
        # Tag extraction is best-effort; on failure return a minimal
        # safe structure so the rest of the pipeline can continue.
        return {
            "artist": None,
            "album_artist": None,
            "album": None,
            "title": None,
            "track": None,
            "genre": None,
            "duration": None,
            "bitrate": None,
            "is_compilation": 0,
            "orig_name": path.stem,
        }


# ================= INGEST =================

def analyze_files(
    src,
    lib,
    db_path,
    progress=False,
    with_fingerprint=False,
    search_covers=False,
    only_states=None,
    exclude_states=None,
):
    """Top-level analysis routine.

    Parameters
    - `src`: path to the source tree to scan for music files
    - `lib`: path to the user's library root used when building
      `recommended_path`
    - `db_path`: path to the SQLite DB file used to persist results
    - `progress`: show a progress bar if `tqdm` is available
    - `with_fingerprint`: enable Chromaprint-based fingerprints
    - `search_covers`: attempt to discover album art for newly seen
      files
    - `only_states` / `exclude_states`: reserved for future filtering

    Behavior summary:
    - Walk the `src` tree and build a list of candidate audio files
    - For each file compute tags, SHA-256 and optionally fingerprint
    - Upsert a row into `files` and add an `actions.move` row when a
      file is first discovered
    - Optionally attempt to ingest album art candidates

    The resulting DB contains both the raw observations and a queue of
    proposed `actions` for a separate executor to apply.
    """

    conn = create_db(db_path)
    c = conn.cursor()

    # Gather all audio files under `src`. Using `rglob` means this is a
    # recursive discovery; `is_audio_file` acts as a fast filter.
    audio_list = [p for p in Path(src).rglob("*") if is_audio_file(p)]
    log({
        "key": MSG_FOUND_AUDIO_FILES,
        "params": {"count": len(audio_list)}
    })

    for p in maybe_progress(audio_list, "Analyzing", progress):
        # Extract tag metadata and compute stable signals
        meta = extract_tags(p)
        sha = sha256_file(p)
        fp = compute_fingerprint(p) if with_fingerprint else None
        rec = recommended_path_for(lib, meta, p.suffix)
        now = utcnow()

        # If we've already seen this original_path, read lifecycle
        # state so we can avoid re-creating duplicate actions.
        row = c.execute(
            "SELECT id, lifecycle_state FROM files WHERE original_path=?",
            (str(p),)
        ).fetchone()

        lifecycle = row["lifecycle_state"] if row else "new"
        is_new = row is None

        # Upsert the file row. We use the `original_path` as the
        # unique key so re-running analysis refreshes metadata while
        # preserving user-assigned lifecycle states when present.
        c.execute("""
            INSERT INTO files (
                original_path, sha256, size_bytes,
                artist, album_artist, album, title, track, genre,
                duration, bitrate, fingerprint,
                is_compilation, recommended_path,
                lifecycle_state,
                first_seen, last_update
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(original_path) DO UPDATE SET
                sha256=excluded.sha256,
                size_bytes=excluded.size_bytes,
                artist=excluded.artist,
                album_artist=excluded.album_artist,
                album=excluded.album,
                title=excluded.title,
                track=excluded.track,
                genre=excluded.genre,
                duration=excluded.duration,
                bitrate=excluded.bitrate,
                fingerprint=excluded.fingerprint,
                is_compilation=excluded.is_compilation,
                recommended_path=excluded.recommended_path,
                last_update=excluded.last_update
        """, (
            str(p), sha, p.stat().st_size,
            meta["artist"], meta["album_artist"],
            meta["album"], meta["title"], meta["track"],
            meta.get("genre"),
            meta["duration"], meta["bitrate"], fp,
            meta["is_compilation"], rec,
            lifecycle,
            now, now
        ))

        # Query back the `id` for convenience and normalization
        file_id = c.execute(
            "SELECT id FROM files WHERE original_path=?",
            (str(p),)
        ).fetchone()[0]

        # Maintain normalized text fields used by DB views for
        # duplicate detection
        normalize_file_row(c, file_id)

        # Create a move action only when the file is first discovered;
        # downstream code is expected to apply or review these actions.
        if is_new:
            c.execute("""
                INSERT INTO actions (
                    file_id, action, src_path, dst_path, created_at
                )
                VALUES (?, 'move', ?, ?, ?)
            """, (file_id, str(p), rec, now))

        if search_covers:
            # If requested, attempt to ingest album art candidates for
            # the album represented by this file.
            file_row = c.execute("""
                SELECT album_artist, album, is_compilation
                FROM files WHERE id=?
            """, (file_id,)).fetchone()

            ingest_album_art_for_file(c, file_row, p)

    conn.commit()
    conn.close()
    log(MSG_ANALYSIS_COMPLETE)

# ================= CLI =================

def main():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--src", required=True)
    parser.add_argument("--lib")
    parser.add_argument("--db")
    parser.add_argument("--progress", action="store_true")
    parser.add_argument("--with-fingerprint", action="store_true")
    parser.add_argument("--search-covers", action="store_true")
    parser.add_argument("--edit-tags", action="store_true")
    parser.add_argument("--only-state")
    parser.add_argument("--exclude-state")

    args = parser.parse_args()

    analyze_files(
        src=args.src,
        lib=resolve_env_path("MUSIC_LIB", args.lib),
        db_path=resolve_database_path(args.db),
        progress=args.progress,
        with_fingerprint=args.with_fingerprint,
        search_covers=args.search_covers,
    )

if __name__ == "__main__":
    main()

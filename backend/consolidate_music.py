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
from backend.normalization import normalize_text
from backend.db_migrations import run_migrations

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

def ensure_export_columns(c):
    ensure_column(c, "files", "export_name_cache", "export_name_cache TEXT")

def ensure_normalized_columns(c):
    ensure_column(c, "files", "artist_norm", "artist_norm TEXT")
    ensure_column(c, "files", "album_artist_norm", "album_artist_norm TEXT")
    ensure_column(c, "files", "album_norm", "album_norm TEXT")
    ensure_column(c, "files", "title_norm", "title_norm TEXT")

def ensure_metadata_columns(c):
    """
    Ensure all optional metadata columns exist.

    This function is additive and idempotent.
    It allows forward-compatible schema upgrades without forcing
    users to rebuild their database.
    """

    ensure_column(c, "files", "composer", "composer TEXT")
    ensure_column(c, "files", "year", "year TEXT")
    ensure_column(c, "files", "bpm", "bpm INTEGER")
    ensure_column(c, "files", "disc", "disc TEXT")
    ensure_column(c, "files", "track_total", "track_total TEXT")
    ensure_column(c, "files", "disc_total", "disc_total TEXT")
    ensure_column(c, "files", "comment", "comment TEXT")
    ensure_column(c, "files", "lyrics", "lyrics TEXT")
    ensure_column(c, "files", "publisher", "publisher TEXT")
    ensure_column(c, "files", "quarantined_path","quarantined_path TEXT")
    ensure_column(c, "files", "quarantined_at","quarantined_at TEXT")
    ensure_column(c, "files", "delete_mode","delete_mode TEXT DEFAULT 'quarantine'")


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

def ensure_mark_delete_column(c):
    cols = [r[1] for r in c.execute("PRAGMA table_info(files)").fetchall()]
    if "mark_delete" not in cols:
        log("Adding mark_delete column to files table")
        c.execute("""
            ALTER TABLE files
            ADD COLUMN mark_delete INTEGER DEFAULT 0
        """)

def ensure_genres_columns(c):
    """
    Ensure optional / forward-compatible columns on `genres`.
    """
    ensure_column(
        c,
        "genres",
        "active",
        "active INTEGER DEFAULT 1"
    )

def ensure_export_tables(c):
    c.execute("""
        CREATE TABLE IF NOT EXISTS export_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            preset_name TEXT NOT NULL,
            preset_hash TEXT NOT NULL,
            target_root TEXT NOT NULL,
            file_count INTEGER NOT NULL,
            total_bytes INTEGER NOT NULL,
            deterministic_hash TEXT NOT NULL,
            created_at TEXT NOT NULL,
            dry_run INTEGER DEFAULT 0
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS export_files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            export_run_id INTEGER NOT NULL,
            file_id INTEGER NOT NULL,
            src_path TEXT NOT NULL,
            dst_path TEXT NOT NULL,
            sha256 TEXT NOT NULL,
            size_bytes INTEGER NOT NULL,
            status TEXT DEFAULT 'planned',
            FOREIGN KEY(export_run_id) REFERENCES export_runs(id),
            FOREIGN KEY(file_id) REFERENCES files(id)
        )
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
    """Create the SQLite schema used by the consolidation pipeline."""

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    # ================= CORE SCHEMA =================
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
        notes TEXT,
        mark_delete INTEGER DEFAULT 0,
        quarantined_path TEXT,
        quarantined_at TEXT,
        delete_mode TEXT DEFAULT 'quarantine'
    );

    CREATE TABLE IF NOT EXISTS export_runs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        preset_name TEXT NOT NULL,
        preset_hash TEXT NOT NULL,
        target_root TEXT NOT NULL,
        file_count INTEGER NOT NULL,
        total_bytes INTEGER NOT NULL,
        deterministic_hash TEXT NOT NULL,
        created_at TEXT NOT NULL,
        dry_run INTEGER DEFAULT 0
    );

    CREATE TABLE IF NOT EXISTS export_files (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        export_run_id INTEGER NOT NULL,
        file_id INTEGER NOT NULL,
        src_path TEXT NOT NULL,
        dst_path TEXT NOT NULL,
        sha256 TEXT NOT NULL,
        size_bytes INTEGER NOT NULL,
        status TEXT DEFAULT 'planned',
        FOREIGN KEY(export_run_id) REFERENCES export_runs(id),
        FOREIGN KEY(file_id) REFERENCES files(id)
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
        created_at TEXT NOT NULL,
        active INTEGER DEFAULT 1
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
                    
    CREATE TABLE IF NOT EXISTS pedro_environment (
        id INTEGER PRIMARY KEY CHECK (id = 1),
        source_root TEXT,
        library_root TEXT,
        schema_version INTEGER NOT NULL,
        created_at TEXT NOT NULL,
        last_update TEXT NOT NULL
    );
                    
    CREATE TABLE IF NOT EXISTS tags (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        normalized_name TEXT NOT NULL UNIQUE,
        source TEXT DEFAULT 'user',
        created_at TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS file_tags (
        file_id INTEGER NOT NULL,
        tag_id INTEGER NOT NULL,
        source TEXT DEFAULT 'user',
        created_at TEXT NOT NULL,
        PRIMARY KEY (file_id, tag_id),
        FOREIGN KEY (file_id) REFERENCES files(id),
        FOREIGN KEY (tag_id) REFERENCES tags(id)
    );

    CREATE INDEX IF NOT EXISTS idx_tags_norm ON tags(normalized_name);
    CREATE INDEX IF NOT EXISTS idx_file_tags_file ON file_tags(file_id);
    CREATE INDEX IF NOT EXISTS idx_file_tags_tag ON file_tags(tag_id);

    CREATE INDEX IF NOT EXISTS idx_genres_norm ON genres(normalized_name);
    CREATE INDEX IF NOT EXISTS idx_file_genres_file ON file_genres(file_id);
    CREATE INDEX IF NOT EXISTS idx_file_genres_genre ON file_genres(genre_id);
    CREATE INDEX IF NOT EXISTS idx_genre_mappings_norm ON genre_mappings(normalized_token);
    CREATE INDEX IF NOT EXISTS idx_genres_active ON genres(active);
    CREATE INDEX IF NOT EXISTS idx_files_lifecycle ON files(lifecycle_state);
    CREATE INDEX IF NOT EXISTS idx_files_size ON files(size_bytes);
    CREATE INDEX IF NOT EXISTS idx_export_runs_hash ON export_runs(deterministic_hash);
    CREATE INDEX IF NOT EXISTS idx_export_files_run ON export_files(export_run_id);
    CREATE INDEX IF NOT EXISTS idx_export_files_file ON export_files(file_id);
    """)

    # Existing additive migrations (your helpers)
    ensure_metadata_columns(c)
    ensure_export_columns(c)
    ensure_normalized_columns(c)
    ensure_genres_columns(c)
    ensure_alias_views(c)
    ensure_mark_delete_column(c)
    ensure_export_tables(c)

    # --- Ensure pedro_environment row exists ---
    row = c.execute(
        "SELECT id FROM pedro_environment WHERE id = 1"
    ).fetchone()

    if not row:
        now = utcnow()
        c.execute("""
            INSERT INTO pedro_environment
            (id, source_root, library_root, schema_version, created_at, last_update)
            VALUES (1, NULL, NULL, 1, ?, ?)
        """, (now, now))

    # ================= NEW: RUN MIGRATIONS =================
    run_migrations(conn)

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
    """Extract tags and technical info from an audio file using Mutagen."""
    try:
        audio = MutagenFile(path, easy=True)
        raw = MutagenFile(path, easy=False)

        album_artist = audio.get("albumartist", [None])[0] if audio else None
        is_comp = 0

        if raw and hasattr(raw, "tags"):
            for k in raw.tags.keys():
                if str(k).lower() in ("tcmp", "compilation", "cpil"):
                    is_comp = 1
                    break

        track_raw = audio.get("tracknumber", [None])[0] if audio else None
        track = normalize_track(track_raw)
        track_total = None
        if track_raw and "/" in str(track_raw):
            parts = str(track_raw).split("/", 1)
            if len(parts) == 2:
                track_total = parts[1]

        disc_raw = audio.get("discnumber", [None])[0] if audio else None
        disc = disc_raw.split("/")[0] if disc_raw and "/" in str(disc_raw) else disc_raw
        disc_total = None
        if disc_raw and "/" in str(disc_raw):
            parts = str(disc_raw).split("/", 1)
            if len(parts) == 2:
                disc_total = parts[1]

        return {
            "artist": audio.get("artist", [None])[0] if audio else None,
            "album_artist": album_artist,
            "album": audio.get("album", [None])[0] if audio else None,
            "title": audio.get("title", [None])[0] if audio else None,

            "track": track,
            "track_total": track_total,
            "disc": disc,
            "disc_total": disc_total,

            # ---------- NEW METADATA ----------
            "composer": audio.get("composer", [None])[0] if audio else None,
            "year": audio.get("date", [None])[0] if audio else None,
            "bpm": (
                int(audio.get("bpm", [None])[0])
                if audio and audio.get("bpm", [None])[0]
                and str(audio.get("bpm", [None])[0]).isdigit()
                else None
            ),
            "comment": audio.get("comment", [None])[0] if audio else None,
            "lyrics": None,
            "publisher": audio.get("publisher", [None])[0] if audio else None,
            # ----------------------------------

            "genre": audio.get("genre", [None])[0] if audio else None,
            "duration": getattr(audio.info, "length", None) if audio else None,
            "bitrate": getattr(audio.info, "bitrate", None) if audio else None,
            "is_compilation": is_comp,
            "orig_name": path.stem,
        }

    except Exception:
        return {
            "artist": None,
            "album_artist": None,
            "album": None,
            "title": None,

            "track": None,
            "track_total": None,
            "disc": None,
            "disc_total": None,

            "composer": None,
            "year": None,
            "bpm": None,
            "comment": None,
            "lyrics": None,
            "publisher": None,

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
    db_mode="full",  # "full" | "schema-only" | "db-update-only" | "normalize-only"
    no_overwrite=False,  # Only used in "db-update-only" mode
    lifecycle_state="ANALYZED",
    create_actions=True,
):
    """Top-level analysis routine."""
    ALLOWED_DB_MODES = {"full", "schema-only", "db-update-only", "normalize-only"}

    if db_mode not in ALLOWED_DB_MODES:
        raise RuntimeError(f"Invalid db_mode: {db_mode}")
    
    conn = create_db(db_path)
    c = conn.cursor()

    # ---------- Persist environment roots (once, correctly) ----------
    now = utcnow()

    if db_mode in ("full", "schema-only", "db-update-only"):
        c.execute("""
            UPDATE pedro_environment
            SET
                source_root = COALESCE(?, source_root),
                library_root = COALESCE(?, library_root),
                last_update = ?
            WHERE id = 1
        """, (
            os.path.abspath(src) if src else None,
            os.path.abspath(lib) if lib else None,
            now,
        ))

    # ---------- SCHEMA-ONLY MODE ----------
    if db_mode == "schema-only":
        log("Schema migration only — no file scanning")
        conn.commit()
        conn.close()
        return

    # ---------- From here on, we REQUIRE src ----------
    if not src:
        raise RuntimeError("src must be provided for db_mode = " + db_mode)
    

    # Gather all audio files
    audio_list = [p for p in Path(src).rglob("*") if is_audio_file(p)]
    log({
        "key": MSG_FOUND_AUDIO_FILES,
        "params": {"count": len(audio_list)}
    })

    # Reserved for future filesystem gating
    allow_filesystem = (db_mode == "full")

    for p in maybe_progress(audio_list, "Analyzing", progress):
        meta = extract_tags(p)

        # ---------- MODE GUARDS ----------
        sha = sha256_file(p) if db_mode != "db-update-only" else None
        fp = compute_fingerprint(p) if (with_fingerprint and db_mode == "full") else None
        rec = recommended_path_for(lib, meta, p.suffix) if db_mode == "full" else None
        now = utcnow()

        row = c.execute(
            "SELECT id, lifecycle_state FROM files WHERE original_path=?",
            (str(p),)
        ).fetchone()

        if row:
            lifecycle = row["lifecycle_state"]
            is_new = False
        else:
            lifecycle = lifecycle_state
            is_new = True

        sql = """
        INSERT INTO files (
            original_path, sha256, size_bytes,
            artist, album_artist, album, title,
            track, track_total,
            disc, disc_total,
            genre, composer, year, bpm, comment, lyrics, publisher,
            duration, bitrate, fingerprint,
            is_compilation, recommended_path,
            lifecycle_state,
            first_seen, last_update,
            notes
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(original_path) DO UPDATE SET
        sha256 = COALESCE(excluded.sha256, sha256),
        size_bytes = COALESCE(excluded.size_bytes, size_bytes),

        artist = CASE
            WHEN excluded.artist IS NOT NULL
                AND ( ? = 0 OR artist IS NULL )
            THEN excluded.artist
            ELSE artist END,

        album_artist = CASE
            WHEN excluded.album_artist IS NOT NULL
                AND ( ? = 0 OR album_artist IS NULL )
            THEN excluded.album_artist
            ELSE album_artist END,

        album = CASE
            WHEN excluded.album IS NOT NULL
                AND ( ? = 0 OR album IS NULL )
            THEN excluded.album
            ELSE album END,

        title = CASE
            WHEN excluded.title IS NOT NULL
                AND ( ? = 0 OR title IS NULL )
            THEN excluded.title
            ELSE title END,

        track = CASE
            WHEN excluded.track IS NOT NULL
                AND ( ? = 0 OR track IS NULL )
            THEN excluded.track
            ELSE track END,

        track_total = CASE
            WHEN excluded.track_total IS NOT NULL
                AND ( ? = 0 OR track_total IS NULL )
            THEN excluded.track_total
            ELSE track_total END,

        disc = CASE
            WHEN excluded.disc IS NOT NULL
                AND ( ? = 0 OR disc IS NULL )
            THEN excluded.disc
            ELSE disc END,

        disc_total = CASE
            WHEN excluded.disc_total IS NOT NULL
                AND ( ? = 0 OR disc_total IS NULL )
            THEN excluded.disc_total
            ELSE disc_total END,

        genre = CASE
            WHEN excluded.genre IS NOT NULL
                AND ( ? = 0 OR genre IS NULL )
            THEN excluded.genre
            ELSE genre END,

        composer = CASE
            WHEN excluded.composer IS NOT NULL
                AND ( ? = 0 OR composer IS NULL )
            THEN excluded.composer
            ELSE composer END,

        year = CASE
            WHEN excluded.year IS NOT NULL
                AND ( ? = 0 OR year IS NULL )
            THEN excluded.year
            ELSE year END,

        bpm = CASE
            WHEN excluded.bpm IS NOT NULL
                AND ( ? = 0 OR bpm IS NULL )
            THEN excluded.bpm
            ELSE bpm END,

        comment = CASE
            WHEN excluded.comment IS NOT NULL
                AND ( ? = 0 OR comment IS NULL )
            THEN excluded.comment
            ELSE comment END,

        lyrics = CASE
            WHEN excluded.lyrics IS NOT NULL
                AND ( ? = 0 OR lyrics IS NULL )
            THEN excluded.lyrics
            ELSE lyrics END,

        publisher = CASE
            WHEN excluded.publisher IS NOT NULL
                AND ( ? = 0 OR publisher IS NULL )
            THEN excluded.publisher
            ELSE publisher END,

        duration = CASE
            WHEN excluded.duration IS NOT NULL
                AND ( ? = 0 OR duration IS NULL )
            THEN excluded.duration
            ELSE duration END,

        bitrate = CASE
            WHEN excluded.bitrate IS NOT NULL
                AND ( ? = 0 OR bitrate IS NULL )
            THEN excluded.bitrate
            ELSE bitrate END,

        fingerprint = CASE
            WHEN excluded.fingerprint IS NOT NULL
                AND ( ? = 0 OR fingerprint IS NULL )
            THEN excluded.fingerprint
            ELSE fingerprint END,

        is_compilation = CASE
            WHEN excluded.is_compilation IS NOT NULL
                AND ( ? = 0 OR is_compilation IS NULL )
            THEN excluded.is_compilation
            ELSE is_compilation END,

        recommended_path = CASE
            WHEN excluded.recommended_path IS NOT NULL
                AND ( ? = 0 OR recommended_path IS NULL )
            THEN excluded.recommended_path
            ELSE recommended_path END,

        last_update = excluded.last_update

                """

        insert_values = (
            str(p),
            sha,
            p.stat().st_size,
            meta["artist"],
            meta["album_artist"],
            meta["album"],
            meta["title"],
            meta["track"],
            meta["track_total"],
            meta["disc"],
            meta["disc_total"],
            meta.get("genre"),
            meta.get("composer"),
            meta.get("year"),
            meta.get("bpm"),
            meta.get("comment"),
            meta.get("lyrics"),
            meta.get("publisher"),
            meta["duration"],
            meta["bitrate"],
            fp,
            meta["is_compilation"],
            rec,
            lifecycle_state,
            now,
            now,
            None,
        )

        overwrite_mode = "no-overwrite" if no_overwrite else "overwrite"

        update_mode_flags = (
            overwrite_mode,  # artist
            overwrite_mode,  # album_artist
            overwrite_mode,  # album
            overwrite_mode,  # title
            overwrite_mode,  # track
            overwrite_mode,  # track_total
            overwrite_mode,  # disc
            overwrite_mode,  # disc_total
            overwrite_mode,  # genre
            overwrite_mode,  # composer
            overwrite_mode,  # year
            overwrite_mode,  # bpm
            overwrite_mode,  # comment
            overwrite_mode,  # lyrics
            overwrite_mode,  # publisher
            overwrite_mode,  # duration
            overwrite_mode,  # bitrate
            overwrite_mode,  # fingerprint
            overwrite_mode,  # is_compilation
            overwrite_mode,  # recommended_path
        )

        assert sql.count("?") == len(insert_values) + len(update_mode_flags)
        c.execute(sql, insert_values + update_mode_flags)

        file_id = c.execute(
            "SELECT id FROM files WHERE original_path=?",
            (str(p),)
        ).fetchone()[0]

        normalize_file_row(c, file_id)

        if is_new and db_mode == "full" and create_actions:
            c.execute("""
                INSERT INTO actions (
                    file_id, action, src_path, dst_path, created_at
                )
                VALUES (?, 'move', ?, ?, ?)
            """, (file_id, str(p), rec, now))

        if search_covers and db_mode == "full":
            file_row = c.execute("""
                SELECT album_artist, album, is_compilation
                FROM files WHERE id=?
            """, (file_id,)).fetchone()

            # ingest_album_art_for_file(c, file_row, p)
    

    conn.commit()
    conn.close()
    log(MSG_ANALYSIS_COMPLETE)

# ================= CLI =================

def main():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--src")
    parser.add_argument("--lib")
    parser.add_argument("--db")
    parser.add_argument("--progress", action="store_true")
    parser.add_argument("--with-fingerprint", action="store_true")
    parser.add_argument("--search-covers", action="store_true")
    parser.add_argument("--edit-tags", action="store_true")
    parser.add_argument("--only-state")
    parser.add_argument("--exclude-state")
    parser.add_argument(
        "--db-mode",
        choices=["full", "schema-only", "db-update-only", "normalize-only"],
        default="full",
        help="Control how Pedro updates the database"
    )
    parser.add_argument("--no-overwrite", action="store_true")

    args = parser.parse_args()

    # Enforce --src only when mode requires scanning
    if args.db_mode not in ("schema-only", "normalize-only") and not args.src:
        parser.error("--src is required unless --db-mode is schema-only or normalize-only")

    analyze_files(
        src=args.src,
        lib=args.lib,
        db_path=args.db,
        progress=args.progress,
        with_fingerprint=args.with_fingerprint,
        search_covers=args.search_covers,
        db_mode=args.db_mode,
        no_overwrite=args.no_overwrite,
    )

if __name__ == "__main__":
    main()

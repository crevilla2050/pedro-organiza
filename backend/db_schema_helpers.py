"""
Pedro Organiza — Schema helper utilities

These are idempotent helpers used by migrations and bootstrapping.
No runtime logic allowed here.
"""

def ensure_column(c, table, column, ddl):
    cols = [r["name"] for r in c.execute(f"PRAGMA table_info({table})")]
    if column not in cols:
        c.execute(f"ALTER TABLE {table} ADD COLUMN {ddl}")


# --------------------------------------------------
# FILES TABLE EXTENSIONS
# --------------------------------------------------

def ensure_metadata_columns(c):
    ensure_column(c, "files", "composer", "composer TEXT")
    ensure_column(c, "files", "year", "year TEXT")
    ensure_column(c, "files", "bpm", "bpm INTEGER")
    ensure_column(c, "files", "disc", "disc TEXT")
    ensure_column(c, "files", "track_total", "track_total TEXT")
    ensure_column(c, "files", "disc_total", "disc_total TEXT")
    ensure_column(c, "files", "comment", "comment TEXT")
    ensure_column(c, "files", "lyrics", "lyrics TEXT")
    ensure_column(c, "files", "publisher", "publisher TEXT")
    ensure_column(c, "files", "quarantined_path", "quarantined_path TEXT")
    ensure_column(c, "files", "quarantined_at", "quarantined_at TEXT")
    ensure_column(c, "files", "delete_mode", "delete_mode TEXT DEFAULT 'quarantine'")


def ensure_normalized_columns(c):
    ensure_column(c, "files", "artist_norm", "artist_norm TEXT")
    ensure_column(c, "files", "album_artist_norm", "album_artist_norm TEXT")
    ensure_column(c, "files", "album_norm", "album_norm TEXT")
    ensure_column(c, "files", "title_norm", "title_norm TEXT")


def ensure_export_columns(c):
    ensure_column(c, "files", "export_name_cache", "export_name_cache TEXT")


def ensure_mark_delete_column(c):
    ensure_column(c, "files", "mark_delete", "mark_delete INTEGER DEFAULT 0")


# --------------------------------------------------
# GENRES
# --------------------------------------------------

def ensure_genres_columns(c):
    ensure_column(c, "genres", "active", "active INTEGER DEFAULT 1")


# --------------------------------------------------
# EXPORT ENGINE
# --------------------------------------------------

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
            status TEXT DEFAULT 'planned'
        )
    """)
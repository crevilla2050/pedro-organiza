# backend/db_migrations.py

"""
Pedro Organiza — Deterministic schema migrations

Philosophy:
- Explicit, linear migrations
- No ORM
- No auto-discovery
- Fully deterministic

Each migration is a function:
    migrate_X_to_Y(conn)

Schema version lives in:
    pedro_environment.schema_version
"""

from datetime import datetime, timezone
from backend.db_schema_helpers import (
    ensure_container_column,
    ensure_metadata_columns,
    ensure_normalized_columns,
    ensure_export_columns,
    ensure_mark_delete_column,
    ensure_genres_columns,
    ensure_export_tables,
)
from backend.db_views import ensure_alias_views

def utcnow():
    return datetime.now(timezone.utc).isoformat()


# ============================================================
# Migration helpers
# ============================================================

def get_code_schema_version():
    return TARGET_SCHEMA_VERSION

def get_schema_version(conn):
    try:
        row = conn.execute(
            "SELECT schema_version FROM pedro_environment WHERE id = 1"
        ).fetchone()
        return row["schema_version"] if row else 0
    except Exception:
        # Table does not exist yet
        return 0


def set_schema_version(conn, version):
    conn.execute(
        """
        UPDATE pedro_environment
        SET schema_version = ?, last_update = ?
        WHERE id = 1
        """,
        (version, utcnow()),
    )

def ensure_environment_table(conn):
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS pedro_environment (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            schema_version INTEGER NOT NULL,
            source_root TEXT,
            library_root TEXT,
            last_update TEXT
        )
    """)

    # Ensure singleton row
    row = c.execute("SELECT COUNT(*) FROM pedro_environment").fetchone()[0]
    if row == 0:
        c.execute("""
            INSERT INTO pedro_environment (id, schema_version)
            VALUES (1, 0)
        """)
        conn.commit()

# ============================================================
# MIGRATIONS
# ============================================================

def migrate_0_to_1(conn):
    """
    Migration v1
    Base Pedro schema (core tables)
    """
    c = conn.cursor()

    c.executescript("""
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

    CREATE TABLE IF NOT EXISTS genres (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        normalized_name TEXT
    );
    
    CREATE TABLE IF NOT EXISTS actions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        file_id INTEGER NOT NULL,
        action TEXT NOT NULL,
        src_path TEXT,
        dst_path TEXT,
        created_at TEXT NOT NULL,
        executed_at TEXT,
        status TEXT DEFAULT 'pending',
        FOREIGN KEY(file_id) REFERENCES files(id)
    );

    CREATE INDEX IF NOT EXISTS idx_actions_file
        ON actions(file_id);

    CREATE INDEX IF NOT EXISTS idx_actions_status
        ON actions(status);
    """)

    conn.commit()

def migrate_1_to_2(conn):
    """
    Migration v2
    Introduces export engine tables.
    """
    c = conn.cursor()

    c.executescript("""
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

    CREATE INDEX IF NOT EXISTS idx_export_runs_hash
        ON export_runs(deterministic_hash);

    CREATE INDEX IF NOT EXISTS idx_export_files_run
        ON export_files(export_run_id);

    CREATE INDEX IF NOT EXISTS idx_export_files_file
        ON export_files(file_id);
    """)
    

def migrate_2_to_3(conn):
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS migration_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            from_version INTEGER,
            to_version INTEGER,
            applied_at TEXT NOT NULL
        )
    """)

def migrate_3_to_4(conn):
    """
    Migration v4
    Multi-library core + schema consolidation
    Fully additive and backward compatible
    """

    c = conn.cursor()

    # ==========================================================
    # MULTI-LIBRARY CORE
    # ==========================================================
    c.executescript("""
    CREATE TABLE IF NOT EXISTS libraries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        root_path TEXT NOT NULL UNIQUE,
        created_at TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS file_library_map (
        file_id INTEGER NOT NULL,
        library_id INTEGER NOT NULL,
        first_seen TEXT NOT NULL,
        last_update TEXT NOT NULL,
        drifted INTEGER DEFAULT 0,
        drifted_at TEXT,
        PRIMARY KEY (file_id, library_id),
        FOREIGN KEY (file_id) REFERENCES files(id),
        FOREIGN KEY (library_id) REFERENCES libraries(id)
    );

    CREATE INDEX IF NOT EXISTS idx_file_library_file
        ON file_library_map(file_id);

    CREATE INDEX IF NOT EXISTS idx_file_library_lib
        ON file_library_map(library_id);
    """)

def migrate_4_to_5(conn):
    """
    Migration v5
    Canonical taxonomy schema upgrade for genres.
    Adds missing canonical fields expected by taxonomy_core.
    """

    c = conn.cursor()

    existing_cols = [r[1] for r in c.execute("PRAGMA table_info(genres)")]

    def ensure_col(name, ddl):
        if name not in existing_cols:
            c.execute(f"ALTER TABLE genres ADD COLUMN {ddl}")

    # Canonical taxonomy columns
    ensure_col("source", "source TEXT DEFAULT 'discovered'")
    ensure_col("created_at", "created_at TEXT")
    ensure_col("updated_at", "updated_at TEXT")

    # Backfill timestamps for legacy rows
    c.execute("""
        UPDATE genres
        SET created_at = COALESCE(created_at, datetime('now'))
    """)

    conn.commit()

def migrate_5_to_6(conn):
    """
    Migration v6
    Introduces full genre taxonomy subsystem.

    Adds:
    - genre_mappings (raw → canonical)
    - file_genres (file ↔ canonical links)
    - supporting indexes
    """

    c = conn.cursor()

    # --------------------------------------------------
    # genre_mappings (raw token normalization layer)
    # --------------------------------------------------
    c.executescript("""
    CREATE TABLE IF NOT EXISTS genre_mappings (
        raw_token TEXT PRIMARY KEY,
        normalized_token TEXT NOT NULL,
        genre_id INTEGER NOT NULL,
        source TEXT DEFAULT 'discovered',
        created_at TEXT NOT NULL,
        FOREIGN KEY (genre_id) REFERENCES genres(id)
    );

    CREATE INDEX IF NOT EXISTS idx_genre_mappings_genre
        ON genre_mappings(genre_id);
    """)

    # --------------------------------------------------
    # file_genres (many-to-many canonical links)
    # --------------------------------------------------
    c.executescript("""
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

    CREATE INDEX IF NOT EXISTS idx_file_genres_file
        ON file_genres(file_id);

    CREATE INDEX IF NOT EXISTS idx_file_genres_genre
        ON file_genres(genre_id);
    """)

    conn.commit()


    # ==========================================================
    # SCHEMA CONSOLIDATION
    # ==========================================================
    from backend.db_schema_helpers import (
        ensure_metadata_columns,
        ensure_normalized_columns,
        ensure_export_columns,
        ensure_mark_delete_column,
        ensure_genres_columns,
        ensure_export_tables,
        ensure_column,
    )
    from backend.db_views import ensure_alias_views

    ensure_metadata_columns(c)
    ensure_normalized_columns(c)
    ensure_export_columns(c)
    ensure_mark_delete_column(c)
    ensure_genres_columns(c)
    ensure_export_tables(c)
    ensure_alias_views(c)

    from backend.db_schema_helpers import ensure_container_column
    ensure_container_column(c)

    # ==========================================================
    # FILES PRESENCE TRACKING (idempotent)
    # ==========================================================
    ensure_column(c, "files", "presence_state", "presence_state TEXT DEFAULT 'present'")
    ensure_column(c, "files", "last_seen", "last_seen TEXT")

    # Backfill presence_state
    c.execute("""
        UPDATE files
        SET presence_state = 'present'
        WHERE presence_state IS NULL
    """)

    conn.commit()

# Ordered migration chain
MIGRATIONS = [
    (0, 1, migrate_0_to_1),
    (1, 2, migrate_1_to_2),
    (2, 3, migrate_2_to_3),
    (3, 4, migrate_3_to_4),
    (4, 5, migrate_4_to_5),
    (5, 6, migrate_5_to_6),
]
TARGET_SCHEMA_VERSION = 6


# ============================================================
# Runner
# ============================================================

def run_migrations(conn, verbose=True):
    
    c = conn.cursor()

    ensure_environment_table(conn)

    # --------------------------------------------------
    # BOOTSTRAP: ensure migration_history exists
    # --------------------------------------------------
    c.execute("""
        CREATE TABLE IF NOT EXISTS migration_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            from_version INTEGER NOT NULL,
            to_version INTEGER NOT NULL,
            applied_at TEXT NOT NULL
        )
    """)

    conn.commit()

    current = get_schema_version(conn)
    

    if verbose:
        print(f"[Pedro] Current schema: {current}")

    for from_v, to_v, fn in MIGRATIONS:
        if current == from_v:
            if verbose:
                print(f"[Pedro] Migrating schema {from_v} → {to_v}")

            fn(conn)

            # Record migration
            conn.execute("""
                INSERT INTO migration_history (from_version, to_version, applied_at)
                VALUES (?, ?, ?)
            """, (from_v, to_v, utcnow()))

            set_schema_version(conn, to_v)
            conn.commit()

            current = to_v

    return current
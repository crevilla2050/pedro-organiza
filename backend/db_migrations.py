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
    ensure_metadata_columns,
    ensure_normalized_columns,
    ensure_export_columns,
    ensure_mark_delete_column,
    ensure_genres_columns,
    ensure_export_tables,
)
from backend.db_views import ensure_alias_views

TARGET_SCHEMA_VERSION = 2

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


# ============================================================
# MIGRATIONS
# ============================================================

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

    # ==========================================================
    # SCHEMA CONSOLIDATION (NEW)
    # Moves schema helpers into migrations layer
    # ==========================================================
    from backend.db_schema_helpers import (
        ensure_metadata_columns,
        ensure_normalized_columns,
        ensure_export_columns,
        ensure_mark_delete_column,
        ensure_genres_columns,
        ensure_export_tables,
    )
    from backend.db_views import ensure_alias_views

    ensure_metadata_columns(c)
    ensure_normalized_columns(c)
    ensure_export_columns(c)
    ensure_mark_delete_column(c)
    ensure_genres_columns(c)
    ensure_export_tables(c)
    ensure_alias_views(c)
    
    c.executescript("""
        ALTER TABLE file_library_map
            ADD COLUMN drifted INTEGER DEFAULT 0;

        ALTER TABLE file_library_map
            ADD COLUMN drifted_at TEXT;
        """)
    # --------------------------------------------
    # Additive columns to files table
    # (safe ALTER pattern)
    # --------------------------------------------
    try:
        c.execute("ALTER TABLE files ADD COLUMN presence_state TEXT DEFAULT 'present'")
    except Exception:
        pass

    try:
        c.execute("ALTER TABLE files ADD COLUMN last_seen TEXT")
    except Exception:
        pass

    # Backfill presence_state if needed
    c.execute("""
        UPDATE files
        SET presence_state = 'present'
        WHERE presence_state IS NULL
    """)

# Ordered migration chain
MIGRATIONS = [
    (1, 2, migrate_1_to_2),
    (2, 3, migrate_2_to_3),
    (3, 4, migrate_3_to_4),
]
TARGET_SCHEMA_VERSION = 4


# ============================================================
# Runner
# ============================================================

def run_migrations(conn, verbose=True):
    c = conn.cursor()

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
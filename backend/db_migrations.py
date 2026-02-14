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

# Ordered migration chain
MIGRATIONS = [
    (1, 2, migrate_1_to_2),
    (2, 3, migrate_2_to_3),
]
TARGET_SCHEMA_VERSION = 3


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
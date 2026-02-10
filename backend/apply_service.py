from backend.lock_service import acquire_lock, release_lock
from backend.config_service import load_config, ensure_quarantine_exists
from backend.active_db import get_active_db
from backend.execute_actions import execute_actions
from pathlib import Path
import sqlite3

from backend.consolidate_music import analyze_files



def apply_actions(
    *,
    dry_run: bool = False,
    permanent_delete: bool = False,
    confirm_permanent: bool = False,
    limit: int | None = None,
    normalize_art: bool = False,
) -> dict:

    lock = acquire_lock("apply")

    try:
        # Ensure runtime configuration is loaded
        load_config()
        ensure_quarantine_exists()
        db_path = get_active_db()
        if not db_path:
            raise RuntimeError("NO_ACTIVE_DB")

        db_path = str(db_path)
        if not Path(db_path).exists():
            raise RuntimeError("ACTIVE_DB_NOT_FOUND")

        # Validate dangerous intent
        if permanent_delete and not confirm_permanent:
            raise RuntimeError(
                "PERMANENT_DELETE_REQUIRES_CONFIRMATION"
            )
        # Ensure DB schema is up to date (no scanning, no filesystem changes)
        analyze_files(
            src=None,
            lib=None,
            db_path=db_path,
            db_mode="schema-only",
        )

        # Flip delete intent at the DB level (never during dry-run)
        if permanent_delete and not dry_run:
            try:
                conn = sqlite3.connect(db_path)
            except sqlite3.Error as e:
                raise RuntimeError(f"DB_CONNECTION_FAILED: {e}")
            try:
                c = conn.cursor()
                c.execute("""
                    UPDATE files
                    SET delete_mode='permanent'
                    WHERE action='delete'
                      AND lifecycle_state NOT IN ('applied','locked')
                """)
                conn.commit()
            finally:
                conn.close()
        
        summary = execute_actions(
            db_path=db_path,
            dry_run=dry_run,
            limit=limit,
            normalize_art=normalize_art,
        )
        return summary
    finally:
        release_lock(lock)



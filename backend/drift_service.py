# backend/drift_service.py

"""
Pedro Organiza — Drift Service

Responsible for detecting and marking files that have disappeared
from a given library since the last scan.

This is part of Pedro's temporal integrity layer.
"""

from datetime import datetime, timezone

def utcnow():
    return datetime.now(timezone.utc).isoformat()


# ============================================================
# Core Drift Marker
# ============================================================

def mark_library_drift(conn, library_id: int, cutoff: str) -> int:
    """
    Marks files as drifted if they were not seen in the current scan.

    Args:
        conn: sqlite connection
        library_id: library being scanned
        cutoff: scan start timestamp (ISO)

    Returns:
        number of files marked as drifted
    """

    cur = conn.cursor()

    # Find mappings that were NOT updated during this scan
    rows = cur.execute(
        """
        SELECT file_id
        FROM file_library_map
        WHERE library_id = ?
        AND last_update < ?
        """,
        (library_id, cutoff),
    ).fetchall()

    drifted = [r[0] for r in rows]

    if not drifted:
        return 0

    now = utcnow()

    # Mark file_library_map entries as drifted
    cur.execute(
        f"""
        UPDATE file_library_map
        SET drifted = 1,
            drifted_at = ?
        WHERE library_id = ?
        AND last_update < ?
        """,
        (now, library_id, cutoff),
    )

    conn.commit()
    return len(drifted)


# ============================================================
# Query Helpers (Future CLI/UI)
# ============================================================

def get_drifted_files(conn, library_id: int):
    return conn.execute(
        """
        SELECT f.id, f.original_path
        FROM file_library_map flm
        JOIN files f ON f.id = flm.file_id
        WHERE flm.library_id = ?
        AND flm.drifted = 1
        """,
        (library_id,),
    ).fetchall()


def clear_drift_for_file(conn, file_id: int, library_id: int):
    conn.execute(
        """
        UPDATE file_library_map
        SET drifted = 0,
            drifted_at = NULL
        WHERE file_id = ?
        AND library_id = ?
        """,
        (file_id, library_id),
    )
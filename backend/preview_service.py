import sqlite3
from backend.active_db import get_active_db


def preview_apply(limit: int | None = None) -> dict:

    db_path = get_active_db()
    if not db_path:
        raise RuntimeError("NO_ACTIVE_DB")

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    try:

        query = """
            SELECT
                a.action,
                COALESCE(f.delete_mode, 'quarantine') AS delete_mode,
                COUNT(*) as count
            FROM actions a
            JOIN files f ON f.id = a.file_id
            WHERE a.status = 'pending'
              AND f.lifecycle_state NOT IN ('applied','locked','error')
            GROUP BY a.action, delete_mode
        """

        rows = conn.execute(query).fetchall()

        summary = {
            "pending_actions": 0,
            "move": 0,
            "archive": 0,
            "delete_quarantine": 0,
            "delete_permanent": 0,
            "skip": 0,
        }

        for r in rows:
            action = r["action"]
            count = r["count"]
            mode = r["delete_mode"]

            summary["pending_actions"] += count

            if action == "delete":
                if mode == "permanent":
                    summary["delete_permanent"] += count
                else:
                    summary["delete_quarantine"] += count
            else:
                summary[action] += count

        if limit:
            summary["limit"] = limit

        return summary

    finally:
        conn.close()

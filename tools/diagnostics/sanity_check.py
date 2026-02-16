#!/usr/bin/env python3
"""
sanity_check.py

Pedro Organiza — Pre-Execution Sanity Audit

Purpose:
- Validate database coherence before execution
- Detect dangerous or inconsistent states
- Provide human-readable diagnostics
- NEVER mutate data

Layer: Safety / Audit
"""

import sqlite3
from collections import Counter
from pathlib import Path
import os
from dotenv import load_dotenv

# ---------------- I18N KEYS ----------------

MSG_HEADER = "SANITY_CHECK_HEADER"
MSG_DB_PATH = "SANITY_DB_PATH"
MSG_TOTAL_FILES = "SANITY_TOTAL_FILES"
MSG_LIFECYCLE_DIST = "SANITY_LIFECYCLE_DISTRIBUTION"
MSG_ACTION_DIST = "SANITY_ACTION_DISTRIBUTION"
MSG_ACTION_STATUS_DIST = "SANITY_ACTION_STATUS_DISTRIBUTION"
MSG_ORPHAN_ACTIONS = "SANITY_ORPHAN_ACTIONS"
MSG_MULTIPLE_PENDING = "SANITY_MULTIPLE_PENDING_ACTIONS"
MSG_MISSING_DST = "SANITY_MISSING_DST"
MSG_SHA_CLUSTERS = "SANITY_SHA_CLUSTERS"
MSG_FP_CLUSTERS = "SANITY_FP_CLUSTERS"
MSG_ERRORS = "SANITY_ERRORS"
MSG_DONE = "SANITY_DONE"

# -------------------------------------------

load_dotenv()

DB_PATH = os.getenv("MUSIC_DB")
if not DB_PATH:
    raise SystemExit({"key": "ERROR_DB_NOT_SET"})


def connect_db():
    if not Path(DB_PATH).exists():
        raise SystemExit({"key": "ERROR_DB_NOT_FOUND", "params": {"path": DB_PATH}})
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def print_section(title_key):
    print("\n" + "=" * 70)
    print(title_key)
    print("=" * 70)


def main():
    print_section(MSG_HEADER)
    print({ "key": MSG_DB_PATH, "params": {"path": DB_PATH} })

    conn = connect_db()
    c = conn.cursor()

    # ---------- Files ----------
    c.execute("SELECT COUNT(*) FROM files")
    total_files = c.fetchone()[0]
    print({ "key": MSG_TOTAL_FILES, "params": {"count": total_files} })

    c.execute("SELECT lifecycle_state FROM files")
    lifecycle = Counter(r["lifecycle_state"] for r in c.fetchall())
    print({ "key": MSG_LIFECYCLE_DIST, "params": dict(lifecycle) })

    # ---------- Actions ----------
    c.execute("SELECT action FROM actions")
    actions = Counter(r["action"] for r in c.fetchall())
    print({ "key": MSG_ACTION_DIST, "params": dict(actions) })

    c.execute("SELECT status FROM actions")
    action_status = Counter(r["status"] for r in c.fetchall())
    print({ "key": MSG_ACTION_STATUS_DIST, "params": dict(action_status) })

    # ---------- Orphan actions ----------
    c.execute("""
        SELECT COUNT(*) FROM actions
        WHERE file_id IS NOT NULL
          AND file_id NOT IN (SELECT id FROM files)
    """)
    orphan_count = c.fetchone()[0]
    if orphan_count:
        print({ "key": MSG_ORPHAN_ACTIONS, "params": {"count": orphan_count} })

    # ---------- Multiple pending actions ----------
    c.execute("""
        SELECT file_id, COUNT(*)
        FROM actions
        WHERE status='pending'
          AND file_id IS NOT NULL
        GROUP BY file_id
        HAVING COUNT(*) > 1
    """)
    multi = c.fetchall()
    if multi:
        print({ "key": MSG_MULTIPLE_PENDING, "params": {"count": len(multi)} })

    # ---------- Missing destination ----------
    c.execute("""
        SELECT COUNT(*) FROM actions
        WHERE action='move'
          AND status='pending'
          AND (dst_path IS NULL OR dst_path='')
    """)
    missing_dst = c.fetchone()[0]
    if missing_dst:
        print({ "key": MSG_MISSING_DST, "params": {"count": missing_dst} })

    # ---------- SHA-256 clusters ----------
    c.execute("""
        SELECT COUNT(*) FROM (
            SELECT sha256
            FROM files
            WHERE sha256 IS NOT NULL
            GROUP BY sha256
            HAVING COUNT(*) > 1
        )
    """)
    sha_clusters = c.fetchone()[0]
    print({ "key": MSG_SHA_CLUSTERS, "params": {"count": sha_clusters} })

    # ---------- Fingerprint clusters ----------
    c.execute("""
        SELECT COUNT(*) FROM (
            SELECT fingerprint
            FROM files
            WHERE fingerprint IS NOT NULL
            GROUP BY fingerprint
            HAVING COUNT(*) > 1
        )
    """)
    fp_clusters = c.fetchone()[0]
    print({ "key": MSG_FP_CLUSTERS, "params": {"count": fp_clusters} })

    # ---------- Errors ----------
    c.execute("""
        SELECT COUNT(*) FROM files
        WHERE lifecycle_state='error'
    """)
    error_files = c.fetchone()[0]
    if error_files:
        print({ "key": MSG_ERRORS, "params": {"count": error_files} })

    conn.close()
    print({ "key": MSG_DONE })


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
review_db.py

Interactive CLI reviewer for Pedro Organiza.

Layer: Review / Planning

Responsibilities:
- Show file metadata + duplicate evidence
- Allow user to PLAN actions (not execute)
- Create or update rows in `actions`
- Append notes safely
- NEVER touch filesystem
"""

import sqlite3
import argparse
from datetime import datetime, timezone
from pathlib import Path
import os
from dotenv import load_dotenv

# ---------------- I18N KEYS ----------------

MSG_REVIEW_START = "REVIEW_START"
MSG_REVIEW_COMPLETE = "REVIEW_COMPLETE"
MSG_NO_FILES = "NO_FILES_TO_REVIEW"
MSG_EXITING = "REVIEW_EXITING"
MSG_INVALID_OPTION = "INVALID_OPTION"
MSG_ACTION_PLANNED = "ACTION_PLANNED"
MSG_NOTE_SAVED = "NOTE_SAVED"
MSG_PATH_UPDATED = "PATH_UPDATED"

MSG_FIELD_PATH = "FIELD_PATH"
MSG_FIELD_ARTIST = "FIELD_ARTIST"
MSG_FIELD_ALBUM = "FIELD_ALBUM"
MSG_FIELD_TITLE = "FIELD_TITLE"
MSG_FIELD_DURATION = "FIELD_DURATION"
MSG_FIELD_BITRATE = "FIELD_BITRATE"
MSG_FIELD_LIFECYCLE = "FIELD_LIFECYCLE"
MSG_FIELD_NOTES = "FIELD_NOTES"
MSG_FIELD_PROPOSED = "FIELD_PROPOSED"
MSG_FIELD_DUPLICATE = "FIELD_DUPLICATE"

MSG_PROMPT_ACTIONS = "PROMPT_ACTIONS"
MSG_PROMPT_NOTE = "PROMPT_NOTE"
MSG_PROMPT_PATH = "PROMPT_PATH"

# ------------------------------------------

load_dotenv()

DB_PATH = os.getenv("MUSIC_DB")
if not DB_PATH:
    raise SystemExit({"key": "ERROR_DB_NOT_SET"})

ACTIONS = {
    "m": "move",
    "s": "skip",
    "d": "delete",
    "a": "archive",
    "n": "note",
    "p": "path",
    "q": "quit",
}

# ---------------- helpers ----------------

def utcnow():
    return datetime.now(timezone.utc).isoformat()

def pretty(v):
    return v if v not in (None, "", "None") else "-"

def connect_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def header(fid):
    print("\n" + "=" * 80)
    print(f"FILE {fid}")
    print("=" * 80)

def emit(key, params=None):
    if params:
        print({"key": key, "params": params})
    else:
        print({"key": key})

# ---------------- queries ----------------

def fetch_candidates(limit=None, only_duplicates=False):
    conn = connect_db()
    c = conn.cursor()

    query = """
        SELECT
            f.id,
            f.original_path,
            f.artist,
            f.album,
            f.title,
            f.duration,
            f.bitrate,
            f.lifecycle_state,
            f.notes,
            f.recommended_path,
            d.reason AS dup_reason,
            d.confidence AS dup_confidence
        FROM files f
        LEFT JOIN duplicates d
          ON f.id = d.file2_id
        WHERE f.lifecycle_state IN ('new','reviewing')
          AND NOT EXISTS (
            SELECT 1 FROM actions
            WHERE actions.file_id = f.id
              AND actions.status = 'pending'
          )
    """

    if only_duplicates:
        query += """
          AND EXISTS (
            SELECT 1 FROM duplicates
            WHERE duplicates.file1_id = f.id
               OR duplicates.file2_id = f.id
          )
        """

    query += " ORDER BY f.id"

    if limit:
        query += f" LIMIT {int(limit)}"

    rows = c.execute(query).fetchall()
    conn.close()
    return rows

# ---------------- review loop ----------------

def review_loop(rows):
    conn = connect_db()
    c = conn.cursor()

    emit(MSG_REVIEW_START, {"count": len(rows)})

    for row in rows:
        fid = row["id"]
        header(fid)

        emit(MSG_FIELD_PATH, {"value": row["original_path"]})
        emit(MSG_FIELD_ARTIST, {"value": pretty(row["artist"])})
        emit(MSG_FIELD_ALBUM, {"value": pretty(row["album"])})
        emit(MSG_FIELD_TITLE, {"value": pretty(row["title"])})
        emit(MSG_FIELD_DURATION, {"value": pretty(row["duration"])})
        emit(MSG_FIELD_BITRATE, {"value": pretty(row["bitrate"])})
        emit(MSG_FIELD_LIFECYCLE, {"value": row["lifecycle_state"]})
        emit(MSG_FIELD_NOTES, {"value": pretty(row["notes"])})
        emit(MSG_FIELD_PROPOSED, {"value": pretty(row["recommended_path"])})

        if row["dup_reason"]:
            emit(MSG_FIELD_DUPLICATE, {
                "reason": row["dup_reason"],
                "confidence": row["dup_confidence"],
            })

        while True:
            emit(MSG_PROMPT_ACTIONS)
            choice = input("> ").strip().lower()

            if choice not in ACTIONS:
                emit(MSG_INVALID_OPTION)
                continue

            action = ACTIONS[choice]

            if action == "quit":
                emit(MSG_EXITING)
                conn.commit()
                conn.close()
                return

            if action == "note":
                emit(MSG_PROMPT_NOTE)
                note = input("> ").strip()
                if note:
                    c.execute("""
                        UPDATE files
                        SET notes = COALESCE(notes,'') || ?
                        WHERE id=?
                    """, (f" | {note}", fid))
                    conn.commit()
                    emit(MSG_NOTE_SAVED)
                continue

            if action == "path":
                emit(MSG_PROMPT_PATH)
                new_path = input("> ").strip()
                if new_path and Path(new_path).suffix:
                    c.execute("""
                        UPDATE files
                        SET recommended_path = ?
                        WHERE id=?
                    """, (new_path, fid))
                    conn.commit()
                    emit(MSG_PATH_UPDATED)
                continue

            # ---- plan action ----
            c.execute("""
                INSERT INTO actions (
                    file_id,
                    action,
                    src_path,
                    dst_path,
                    status,
                    created_at
                )
                VALUES (?, ?, ?, ?, 'pending', ?)
            """, (
                fid,
                action,
                row["original_path"],
                row["recommended_path"],
                utcnow()
            ))

            c.execute("""
                UPDATE files
                SET lifecycle_state='reviewing'
                WHERE id=?
            """, (fid,))

            conn.commit()
            emit(MSG_ACTION_PLANNED, {"action": action})
            break

    conn.close()
    emit(MSG_REVIEW_COMPLETE)

# ---------------- CLI ----------------

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int)
    parser.add_argument("--only-duplicates", action="store_true")
    args = parser.parse_args()

    rows = fetch_candidates(
        limit=args.limit,
        only_duplicates=args.only_duplicates
    )

    if not rows:
        emit(MSG_NO_FILES)
        return

    review_loop(rows)

if __name__ == "__main__":
    main()

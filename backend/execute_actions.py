#!/usr/bin/env python3
"""
backend/execute_actions.py

Execution engine (Layer 3 – Hands)

This module applies filesystem actions that were previously planned and
recorded in the application's SQLite database. Actions are read from the
`files` table and applied deterministically: moves, archives, soft-deletes
(move to a trash folder), and user-requested skips (lock the file). The
module deliberately avoids re-analyzing tags or making destination
guesses — it treats the database as the single source of truth for what
should happen.

Behaviour notes:
- Actions are applied one-by-one and the database is updated immediately
    to reflect lifecycle changes (`applied`, `locked`, `error`).
- Optional album-art normalization runs after move/archive operations if
    `--normalize-art` is supplied and the `resize_images.normalize_image`
    function is available.
- All user-facing strings are loaded from i18n JSON files; keys are used
    throughout the code so the runtime is language-independent.
"""

import sqlite3
import argparse
import shutil
from pathlib import Path
from datetime import datetime, timezone
import os
import json
from dotenv import load_dotenv

from backend.config_service import ensure_quarantine_exists


# Optional album art normalization
try:
    from backend.resize_images import normalize_image
except Exception:
    normalize_image = None


# ================= CONFIG =================

load_dotenv()

DB_PATH = os.getenv("MUSIC_DB")
if not DB_PATH:
    raise SystemExit("MUSIC_DB_NOT_SET")

I18N_LANG = os.getenv("PEDRO_LANG", "en")
I18N_PATH = Path("music-ui/src/i18n") / f"{I18N_LANG}.json"


# ================= I18N =================

def load_messages():
    if I18N_PATH.exists():
        try:
            with open(I18N_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

_MESSAGES = load_messages()

def msg(key: str) -> str:
    return _MESSAGES.get(key, key)


# ================= UTILITIES =================

def utcnow():
    """Return current UTC time as an ISO-8601 string for timestamps.

    Used to mark `last_update`, `applied_at`, and `created_at` fields in
    the database so the operation is auditable.
    """
    return datetime.now(timezone.utc).isoformat()

def log(key, **kwargs):
    """Localized timestamped logging helper.

    `key` is an i18n message key; `kwargs` are formatting parameters for
    the message. Failures during formatting are swallowed to avoid
    interrupting execution.
    """
    text = msg(key)
    if kwargs:
        try:
            text = text.format(**kwargs)
        except Exception:
            pass
    print(f"[{utcnow()}] {text}")

def connect_db(path):
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn

def ensure_parent(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)


# ================= ALBUM ART NORMALIZATION =================

def normalize_album_art_in_dir(
    album_dir: Path,
    *,
    max_size: int = 1024,
    min_size: int = 300,
):
    """Optionally normalize album-art files inside `album_dir`.

    This is a best-effort helper: if the optional `normalize_image`
    import is missing or normalization fails for a single file, we ignore
    the error and continue. Only common image extensions are processed.
    """
    if not normalize_image:
        return

    if not album_dir.exists() or not album_dir.is_dir():
        return

    for p in album_dir.iterdir():
        if not p.is_file():
            continue
        if p.suffix.lower() not in {".jpg", ".jpeg", ".png", ".webp"}:
            continue
        try:
            normalize_image(
                p,
                max_size=max_size,
                min_size=min_size,
                allow_upscale=False,
            )
        except Exception:
            # Be permissive: art normalization is optional and should not
            # break file operations.
            pass


# ================= CORE EXECUTION =================

def execute_actions(
    db_path,
    *,
    archive_root=None,
    trash_root="to_trash",
    dry_run=False,
    limit=None,
    normalize_art=False,
):
    trash_root = ensure_quarantine_exists()
    if archive_root:
        archive_root = Path(archive_root).resolve()

    conn = connect_db(db_path)
    c = conn.cursor()
    c.execute("PRAGMA foreign_keys = ON")

    # Select pending filesystem actions from the `files` table. We only
    # consider explicit actions that were planned previously by the
    # application logic: 'move', 'archive', 'delete', 'skip'. Files that
    # are already 'applied' or 'locked' are skipped.
    query = """
        SELECT
            id,
            original_path,
            recommended_path,
            action,
            lifecycle_state
        FROM files
        WHERE action IN ('move','archive','delete','skip')
          AND lifecycle_state NOT IN ('applied','locked')
    """

    if limit:
        query += f" LIMIT {int(limit)}"

    rows = c.execute(query).fetchall()
    log("EXEC_LOADED_ACTIONS", count=len(rows), dry_run=dry_run)

    # Execution counters for a final summary
    summary = {
        "moved": 0,
        "archived": 0,
        "deleted": 0,
        "skipped": 0,
        "errors": 0,
    }

    for row in rows:
        fid = row["id"]
        action = row["action"]
        src = Path(row["original_path"]) if row["original_path"] else None

        try:
            if not src or not src.exists():
                # Missing source is a fatal condition for this row
                raise RuntimeError("SOURCE_MISSING")

            # ---------------- MOVE ----------------
            if action == "move":
                if not row["recommended_path"]:
                    raise RuntimeError("MISSING_RECOMMENDED_PATH")

                dst = Path(row["recommended_path"])
                ensure_parent(dst)

                log("EXEC_MOVE", src=src, dst=dst)
                if not dry_run:
                    shutil.move(src, dst)

                # Optionally normalize album art in the destination folder
                if normalize_art:
                    normalize_album_art_in_dir(dst.parent)

                # Mark as applied and update path + timestamp
                c.execute("""
                    UPDATE files
                    SET original_path=?,
                        lifecycle_state='applied',
                        last_update=?
                    WHERE id=?
                """, (str(dst), utcnow(), fid))

                summary["moved"] += 1

            # ---------------- ARCHIVE ----------------
            elif action == "archive":
                if not archive_root:
                    raise RuntimeError("ARCHIVE_ROOT_NOT_SET")

                dst = archive_root / src.name
                ensure_parent(dst)

                log("EXEC_ARCHIVE", src=src, dst=dst)
                if not dry_run:
                    shutil.move(src, dst)

                if normalize_art:
                    normalize_album_art_in_dir(dst.parent)

                c.execute("""
                    UPDATE files
                    SET original_path=?,
                        lifecycle_state='applied',
                        last_update=?
                    WHERE id=?
                """, (str(dst), utcnow(), fid))

                summary["archived"] += 1

            # ---------------- DELETE (SOFT) ----------------
            elif action == "delete":
                delete_mode = row.get("delete_mode", "quarantine")

                if delete_mode == "permanent":
                    log("EXEC_DELETE_PERMANENT", src=src)
                    if not dry_run:
                        src.unlink()

                    c.execute("""
                        UPDATE files
                        SET lifecycle_state='applied',
                            last_update=?
                        WHERE id=?
                    """, (utcnow(), fid))

                else:
                    dst = trash_root / src.name
                    ensure_parent(dst)

                    log("EXEC_TRASH", src=src, dst=dst)
                    if not dry_run:
                        shutil.move(src, dst)

                    c.execute("""
                        UPDATE files
                        SET original_path=?,
                            lifecycle_state='applied',
                            last_update=?
                        WHERE id=?
                    """, (str(dst), utcnow(), fid))

                summary["deleted"] += 1

            # ---------------- SKIP ----------------
            elif action == "skip":
                # Lock the file so it won't be proposed for actions again
                log("EXEC_SKIP", src=src)
                c.execute("""
                    UPDATE files
                    SET lifecycle_state='locked',
                        last_update=?
                    WHERE id=?
                """, (utcnow(), fid))
                summary["skipped"] += 1

            # Persist the per-row changes immediately so progress is
            # visible to other processes.
            conn.commit()

        except Exception as e:
            # On any failure, record the error on the file row and continue
            err = str(e)
            log("EXEC_ERROR", id=fid, error=err)
            c.execute("""
                UPDATE files
                SET lifecycle_state='error',
                    last_update=?,
                    notes=COALESCE(notes,'') || ?
                WHERE id=?
            """, (utcnow(), f" | exec_error:{err}", fid))
            conn.commit()
            summary["errors"] += 1

    conn.close()

    log("EXEC_FINISHED")
    for k, v in summary.items():
        log("EXEC_SUMMARY_LINE", key=k, value=v)


# ================= CLI =================

def main():
    parser = argparse.ArgumentParser(description="Execute planned filesystem actions")
    parser.add_argument("--db", default=DB_PATH)
    parser.add_argument("--archive-root")
    parser.add_argument("--trash-root", default="to_trash")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--limit", type=int)
    parser.add_argument(
        "--normalize-art",
        action="store_true",
        help="Normalize album art after move/archive"
    )

    args = parser.parse_args()

    execute_actions(
        db_path=args.db,
        archive_root=args.archive_root,
        trash_root=args.trash_root,
        dry_run=args.dry_run,
        limit=args.limit,
        normalize_art=args.normalize_art,
    )


if __name__ == "__main__":
    main()

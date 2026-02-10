# cli/main.py

import argparse
import sqlite3
import os
import json

from backend.i18n.messages import msg
from cli.genres import register_genres_commands, handle_genres

from backend.db_state import set_active_db, get_active_db, clear_active_db
from backend.startup_service import inspect_pedro_db


def main():
    parser = argparse.ArgumentParser(
        prog="pedro",
        description="Pedro Organiza CLI"
    )

    parser.add_argument(
        "--lang",
        default="en",
        help="Language"
    )

    parser.add_argument(
        "--raw",
        action="store_true",
        help="Raw (non-localized) output"
    )

    subparsers = parser.add_subparsers(
        dest="command",
        required=True
    )

    # ---------------- DB commands ----------------
    subparsers.add_parser("db-set").add_argument("path")
    subparsers.add_parser("db-show-active")
    subparsers.add_parser("db-clear")

    # ---------------- STATUS ----------------
    status = subparsers.add_parser(
        "status",
        help="Show current Pedro database status"
    )
    status.add_argument(
        "--json",
        action="store_true",
        help="Output machine-readable JSON"
    )

    # ---------------- SCAN ----------------
    scan = subparsers.add_parser(
        "scan",
        help = argparse.SUPPRESS,  
        description=argparse.SUPPRESS
    )
    

    # ---------------- ANALYZE (alias for scan) ----------------
    analyze = subparsers.add_parser(
        "analyze",
        help="Analyze music library and update database",
        description=scan.description
    )

    analyze.add_argument("--src", help="Source music directory")
    analyze.add_argument("--lib", help="Canonical library root")
    analyze.add_argument(
        "--db-mode",
        choices=["full", "schema-only", "db-update-only", "normalize-only"],
        default="full",
        help="Database update mode"
    )
    analyze.add_argument(
        "--with-fingerprint",
        action="store_true",
        help="Enable audio fingerprinting"
    )
    analyze.add_argument(
        "--search-covers",
        action="store_true",
        help="Search for album art"
    )
    analyze.add_argument(
        "--no-overwrite",
        action="store_true",
        help="Do not overwrite existing metadata"
    )

    # ---------------- GENRES ----------------
    register_genres_commands(subparsers)

    # ---------------- APPLY ----------------
    apply_parser = subparsers.add_parser(
        "apply",
        help="Apply pending filesystem actions"
    )

    apply_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate execution without modifying files"
    )
    
    apply_parser.add_argument(
        "--preview", 
        action="store_true",
        help="Simulate execution without modifying files"
    )

    apply_parser.add_argument(
        "--limit",
        type=int,
        help="Limit number of actions"
    )

    apply_parser.add_argument(
        "--delete-permanent",
        action="store_true",
        help="Permanently delete files instead of quarantining"
    )

    apply_parser.add_argument(
        "--yes-i-know-what-im-doing",
        action="store_true",
        dest="confirm_permanent",
        help="Required to enable permanent deletion"
    )

    apply_parser.add_argument(
        "--trash-root",
        help="Override quarantine directory for this run"
    )

    apply_parser.add_argument(
        "--normalize-art",
        action="store_true",
        help="Normalize album art after move/archive"
    )

    # ---------------- Parse args ----------------
    args = parser.parse_args()

    # ---------------- DB commands ----------------
    if args.command == "db-set":
        set_active_db(args.path)
        print(f"{msg('DB_SET')}: {args.path}")
        return

    if args.command == "db-show-active":
        db = get_active_db()
        if db:
            print(f"{msg('DB_ACTIVE')}: {db}")
        else:
            print(msg("NO_ACTIVE_DB"))
        return

    if args.command == "db-clear":
        clear_active_db()
        print(msg("DB_CLEARED"))
        return

    # ---------------- STATUS ----------------
    if args.command == "status":
        db_path = get_active_db()

        result = {
            "active_db": db_path,
            "exists": False,
            "is_pedro_db": False,
            "files": None,
            "genres": None,
        }

        if not db_path:
            if args.json:
                print(json.dumps(result, indent=2))
            else:
                print(msg("NO_ACTIVE_DB"))
            return

        result["exists"] = os.path.exists(db_path)

        if not result["exists"]:
            if args.json:
                print(json.dumps(result, indent=2))
            else:
                print(msg("DB_FILE_NOT_FOUND"))
            return

        try:
            info = inspect_pedro_db(db_path)
        except Exception as e:
            result["error"] = str(e)
            if args.json:
                print(json.dumps(result, indent=2))
            else:
                print(msg("DB_INSPECTION_FAILED"))
            return

        result["is_pedro_db"] = info.get("is_pedro_db", False)

        if not result["is_pedro_db"]:
            if args.json:
                print(json.dumps(result, indent=2))
            else:
                print(msg("NOT_PEDRO_DB"))
            return

        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        try:
            result["files"] = conn.execute(
                "SELECT COUNT(*) AS c FROM files"
            ).fetchone()["c"]

            result["genres"] = conn.execute(
                "SELECT COUNT(*) AS c FROM genres"
            ).fetchone()["c"]
        finally:
            conn.close()

        if args.json:
            print(json.dumps(result, indent=2))
        else:
            print(msg("PEDRO_DB_OK"))
            print(f"{msg('FILES_COUNT')}: {result['files']}")
            print(f"{msg('GENRES_COUNT')}: {result['genres']}")

        return

    # ---------------- Commands that require DB ----------------
    db_path = get_active_db()
    if not db_path or not os.path.exists(db_path):
        print(msg("MUSIC_DB_NOT_SET"))
        return

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    try:
        if args.command == "genres":
            handle_genres(args, conn)

        elif args.command in ("scan", "analyze"):
            from backend.consolidate_music import analyze_files

            analyze_files(
                src=args.src,
                lib=args.lib,
                db_path=db_path,
                progress=True,
                with_fingerprint=args.with_fingerprint,
                search_covers=args.search_covers,
                db_mode=args.db_mode,
                no_overwrite=args.no_overwrite,
            )
        elif args.command == "apply":

            # ---------- PREVIEW (read-only, no locks, no engine) ----------
            if args.preview:
                from backend.preview_service import preview_apply

                result = preview_apply(limit=args.limit)
                print(json.dumps(result, indent=2))
                return

            # ---------- APPLY / DRY-RUN ----------
            from backend.apply_service import apply_actions

            try:
                summary = apply_actions(
                    dry_run=args.dry_run,
                    permanent_delete=args.delete_permanent,
                    confirm_permanent=args.confirm_permanent,
                    limit=args.limit,
                    normalize_art=args.normalize_art,
                    trash_root=args.trash_root,
                )

                print(json.dumps(summary, indent=2))

            except RuntimeError as e:
                print(str(e))
                return
            
            print(json.dumps(summary, indent=2))
    finally:
        conn.close()


if __name__ == "__main__":
    main()

# cli/main.py

import argparse
import sqlite3
import os
import json

from backend.i18n.messages import msg
from cli.genres import register_genres_commands, handle_genres
from cli.export_cli import register_export_subparser

from backend.db_state import set_active_db, get_active_db, clear_active_db
from backend.startup_service import inspect_pedro_db
from backend.diagnostics import write_diagnostic_report

import importlib.metadata

def main():
    parser = argparse.ArgumentParser(
        prog="pedro",
        description="Pedro Organiza — deterministic music library management",
        epilog="""
            Examples:

            pedro db set music.db
            pedro analyze --src ~/Downloads --lib ~/Music
            pedro preview
            pedro apply --dry-run
            """
    )

    parser.add_argument(
        "--lang",
        default="en",
        help="Override UI language (en, es, de)"
    )

    parser.add_argument(
        "--raw",
        action="store_true",
        help="Raw (non-localized) output"
    )

    parser.add_argument(
        "--diagnostic-file",
        help="Write diagnostic report to file (optional path)"
    )

    subparsers = parser.add_subparsers(
        dest="command",
        required=True
    )

    subparsers.add_parser(
        "version",
        help="Show Pedro version"
    )

    subparsers.add_parser(
        "migrate",
        help="Run deterministic database migrations"
    )

    subparsers.add_parser(
        "doctor",
        help="Run Pedro system health checks"
    )

    register_export_subparser(subparsers)

    # ---------------- DB commands ----------------
    db_parser = subparsers.add_parser(
        "db",
        help="Database management"
    )

    db_sub = db_parser.add_subparsers(dest="db_cmd", required=True)

    db_set = db_sub.add_parser("set", help="Set active database")
    db_set.add_argument("path")

    db_sub.add_parser("show-active", help="Show active database")
    db_sub.add_parser("clear", help="Clear active database")

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
    analyze = subparsers.add_parser(
        "analyze",
        aliases=["scan"],
        help="Analyze music library and update database"
    )

    # ---------------- ANALYZE (alias for scan) ----------------

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

    # ---------------- PREVIEW ----------------
    preview_parser = subparsers.add_parser(
        "preview",
        help="Preview pending filesystem actions (read-only)"
    )
    preview_parser.add_argument("--limit", type=int)

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
        "--limit",
        type=int,
        help="Limit number of actions"
    )
    
    apply_parser.add_argument(
        "--create-trash-root",
        action="store_true",
        help="Allow automatic creation of the override trash directory"
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
    if args.command == "version":
        print(importlib.metadata.version("pedro-organiza"))
        return
    
    # Generic subcommand handler (for modular CLIs)
    if hasattr(args, "func"):
        args.func(args)
        return

    # ---------------- DB commands ----------------
    if args.command == "db":
        if args.db_cmd == "set":
            set_active_db(args.path)
            print(f"{msg('DB_SET')}: {args.path}")
            return

        if args.db_cmd == "show-active":
            db = get_active_db()
            if db:
                print(f"{msg('DB_ACTIVE')}: {db}")
            else:
                print(msg("NO_ACTIVE_DB"))
            return

        if args.db_cmd == "clear":
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
            "schema_version": None,
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

            schema = conn.execute(
                "SELECT schema_version FROM pedro_environment WHERE id=1"
            ).fetchone()["schema_version"]
            result["schema_version"] = schema
        
            from backend.db_migrations import get_code_schema_version

            code_schema = get_code_schema_version()
            result["code_schema_version"] = code_schema

            if result["schema_version"] < code_schema:
                result["schema_outdated"] = True
            else:
                result["schema_outdated"] = False
            
            if result["schema_version"] < result["code_schema_version"]:
                print("⚠ Schema is outdated — run: pedro migrate")
            
            if result["schema_version"] > result["code_schema_version"]:
                result["schema_ahead"] = True
            else:
                result["schema_ahead"] = False
            
            if result.get("schema_ahead"):
                print("⚠ Database schema is newer than this Pedro version")
                print("   Consider upgrading Pedro.")

        finally:
            conn.close()

        if args.json:
            print(json.dumps(result, indent=2))
        else:
            print(msg("PEDRO_DB_OK"))
            print(f"{msg('FILES_COUNT')}: {result['files']}")
            print(f"{msg('GENRES_COUNT')}: {result['genres']}")
            print(f"{msg('SCHEMA_VERSION')}: {result['schema_version']}")

        return

    # ---------------- Commands that require DB ----------------
    # ---------------- Commands that require DB ----------------
    db_path = get_active_db()

    # Commands that are allowed to bootstrap a new DB
    BOOTSTRAP_COMMANDS = {"analyze", "scan"}

    if not db_path:
        print(msg("MUSIC_DB_NOT_SET"))
        return

    # If DB path exists but file doesn't:
    # Allow analyze to create it, block everything else
    if not os.path.exists(db_path) and args.command not in BOOTSTRAP_COMMANDS:
        print(msg("DB_FILE_NOT_FOUND"))
        return

    from backend.paths import BASE_CONFIG_DIR
    from pathlib import Path
    import datetime

    if args.command in ("doctor", "status") or args.diagnostic_file is not None:
        from pathlib import Path
        from datetime import datetime
        from backend.paths import BASE_CONFIG_DIR
        from backend.diagnostics import write_diagnostic_report

        # Decide output path
        if args.diagnostic_file:
            out_path = args.diagnostic_file
        else:
            ts = datetime.now().strftime("%Y%m%d-%H%M%S")
            out_path = str(Path(BASE_CONFIG_DIR) / f"diagnostic-{ts}.json")

        # Generate diagnostic
        hash_value = write_diagnostic_report(db_path, out_path)

        print(f"Diagnostic written to: {out_path}")
        print(f"Deterministic hash: {hash_value}")


    # ---------- GENRES ----------
    if args.command == "genres":
        with sqlite3.connect(db_path) as conn:
            conn.row_factory = sqlite3.Row
            handle_genres(args, conn)
        return


    # ---------- ANALYZE ----------
    elif args.command == "analyze":
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
        return

    # ---------- PREVIEW ----------
    elif args.command == "preview":
        from backend.preview_service import preview_apply

        result = preview_apply(limit=getattr(args, "limit", None))
        print(json.dumps(result, indent=2))
        return

    # ---------- APPLY ----------
    elif args.command == "apply":

        from backend.apply_service import apply_actions

        try:
            summary = apply_actions(
                dry_run=args.dry_run,
                permanent_delete=args.delete_permanent,
                confirm_permanent=args.confirm_permanent,
                limit=args.limit,
                normalize_art=args.normalize_art,
                trash_root=args.trash_root,
                allow_create_trash=args.create_trash_root,
            )

            print(json.dumps(summary, indent=2))

        except RuntimeError as e:
            print(str(e))

        return
    
    elif args.command == "migrate":
        from backend.db_migrations import run_migrations

        # ---------------- Commands that require DB ----------------
        db_path = get_active_db()

        # Commands that REQUIRE an existing DB file
        commands_requiring_existing_db = {"preview", "apply", "genres", "status", "doctor", "migrate"}

        if not db_path:
            print(msg("MUSIC_DB_NOT_SET"))
            return

        if args.command in commands_requiring_existing_db and not os.path.exists(db_path):
            print(msg("DB_FILE_NOT_FOUND"))
            return

        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        try:
            final = run_migrations(conn, verbose=True)
            print(f"Schema now at version {final}")
        finally:
            conn.close()
        return


if __name__ == "__main__":
    main()

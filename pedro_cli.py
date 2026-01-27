#!/usr/bin/env python3
# pedro_cli.py

import argparse
import json
import sys

from backend.startup_service import (
    inspect_pedro_db,
    dry_run_migration,
    activate_pedro_db,
    rescan_pedro_db,
    inspect_target_dir,
)

# -------------------------------------------------
# Helpers
# -------------------------------------------------

def print_json(data):
    print(json.dumps(data, indent=2, ensure_ascii=False))


def die(msg_key):
    print_json({
        "status": "error",
        "warnings": [msg_key],
    })
    sys.exit(1)


# -------------------------------------------------
# Startup Commands
# -------------------------------------------------

def cmd_startup_inspect(args):
    if not args.db:
        die("NO_DB_PROVIDED")

    result = inspect_pedro_db(args.db)
    print_json(result)


def cmd_startup_dry_run(args):
    if not args.db:
        die("NO_DB_PROVIDED")

    result = dry_run_migration(args.db)
    print_json(result)


def cmd_startup_activate(args):
    if not args.db:
        die("NO_DB_PROVIDED")

    result = activate_pedro_db(args.db)
    print_json(result)


def cmd_startup_rescan(args):
    if not args.src:
        die("SRC_NOT_PROVIDED")

    payload = {
        "src": args.src,
        "db_mode": args.db_mode,
        "progress": args.progress,
    }

    result = rescan_pedro_db(payload)
    print_json(result)

def cmd_startup_inspect_target(args):
    if not args.src:
        die("SRC_NOT_PROVIDED")

    if not args.dst:
        die("DST_NOT_PROVIDED")

    result = inspect_target_dir(args.src, args.dst)
    print_json(result)


# -------------------------------------------------
# CLI Definition
# -------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        prog="pedro",
        description="Pedro Organiza — Command Line Interface",
    )

    subparsers = parser.add_subparsers(dest="group", required=True)

    # =============================
    # startup group
    # =============================

    startup = subparsers.add_parser("startup", help="Startup / onboarding commands")
    startup_sub = startup.add_subparsers(dest="command", required=True)

    # --- inspect-db ---
    p_inspect = startup_sub.add_parser("inspect-db", help="Inspect a candidate database")
    p_inspect.add_argument("--db", required=True, help="Path to database file")
    p_inspect.set_defaults(func=cmd_startup_inspect)

    # --- inspect-target ---
    inspect_target_parser = startup_sub.add_parser("inspect-target", help="Inspect target directory safety")
    inspect_target_parser.add_argument("--src", required=True, help="Source music directory")
    inspect_target_parser.add_argument("--dst", required=True, help="Target directory")
    inspect_target_parser.set_defaults(func=cmd_startup_inspect_target)

    # --- dry-run ---
    p_dry = startup_sub.add_parser("dry-run", help="Dry-run database migration")
    p_dry.add_argument("--db", required=True, help="Path to database file")
    p_dry.set_defaults(func=cmd_startup_dry_run)

    # --- activate-db ---
    p_activate = startup_sub.add_parser("activate-db", help="Activate a database")
    p_activate.add_argument("--db", required=True, help="Path to database file")
    p_activate.set_defaults(func=cmd_startup_activate)

    # --- rescan ---
    p_rescan = startup_sub.add_parser("rescan", help="Rescan existing database")
    p_rescan.add_argument("--src", required=True, help="Source music directory")
    p_rescan.add_argument(
        "--db-mode",
        default="full",
        choices=["full", "schema-only", "db-update-only", "normalize-only", "no-overwrite"],
        help="Rescan mode",
    )
    p_rescan.add_argument(
        "--progress",
        action="store_true",
        help="Show progress bar",
    )
    p_rescan.set_defaults(func=cmd_startup_rescan)

    # =============================
    # Execute
    # =============================

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()

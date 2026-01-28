# cli/main.py

import argparse
import sqlite3
import os

from backend.i18n.messages import msg
from cli.genres import register_genres_commands, handle_genres

from backend.db_state import set_active_db, get_active_db, clear_active_db
from backend.i18n.messages import msg


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

    subparsers.add_parser("db-set").add_argument("path")
    subparsers.add_parser("db-show-active")
    subparsers.add_parser("db-clear")

    # Register future command groups
    register_genres_commands(subparsers)

    # Parse args
    args = parser.parse_args()

    # Handle DB commands
    if args.command == "db-set":
        set_active_db(args.path)
        print(f"{msg('DB_SET')}: {args.path}")

    elif args.command == "db-show-active":
        db = get_active_db()
        if db:
            print(f"{msg('DB_ACTIVE')} {db}")
        else:
            print(msg("NO_ACTIVE_DB"))

    elif args.command == "db-clear":
        clear_active_db()
        print(msg("DB_CLEARED"))

    # Resolve DB
    db_path = get_active_db()
    if not db_path or not os.path.exists(db_path):
        print(msg("MUSIC_DB_NOT_SET"))
        return

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    try:
        if args.command == "genres":
            handle_genres(args, conn)
    finally:
        conn.close()


if __name__ == "__main__":
    main()

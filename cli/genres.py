# cli/genres.py

from backend.genre_service import (
    list_genres,
    find_empty_genres,
    purge_empty_genres,
)

from backend.genre_discovery import discover_genres
from backend.i18n.messages import msg
from backend.genre_service import normalize_genres

def register_genres_commands(subparsers):
    genres = subparsers.add_parser(
        "genres",
        help="Manage and inspect genres"
    )

    genres_sub = genres.add_subparsers(
        dest="genres_command",
        required=True
    )

    # ----------------------------
    # genres list
    # ----------------------------

    list_cmd = genres_sub.add_parser(
        "list",
        help="List canonical genres (supports wildcards *, ?)"
    )

    list_cmd.add_argument(
        "pattern",
        nargs="?",
        default="*",
        help="Wildcard pattern (e.g. '*metal*')"
    )

    # ----------------------------
    # genres discover
    # ----------------------------

    discover_cmd = genres_sub.add_parser(
        "discover",
        help="Discover genres from file metadata and populate canonical tables"
    )

    discover_cmd.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without modifying the database"
    )

    discover_cmd.add_argument(
        "--clear-previous",
        action="store_true",
        help="Clear existing genre mappings before discovery"
    )

    # ----------------------------
    # genres normalize (stub for now)
    # ----------------------------

    normalize_cmd = genres_sub.add_parser(
        "normalize",
        help="Normalize multiple genres into a canonical one"
    )

    normalize_cmd.add_argument(
        "genres",
        nargs="+",
        help="Exact genre names to normalize (no wildcards)"
    )

    normalize_cmd.add_argument(
        "--to",
        required=True,
        help="Target canonical genre name"
    )

    normalize_cmd.add_argument(
        "--apply-genres",
        action="store_true",
        help="Apply changes to the database (otherwise preview only)"
    )

    normalize_cmd.add_argument(
        "--clear-previous",
        action="store_true",
        help="Replace existing genres instead of appending"
    )

    cleanup_cmd = genres_sub.add_parser(
        "cleanup",
        help="Inspect or purge empty (unused) genres"
    )

    cleanup_cmd.add_argument(
        "--list-empty",
        action="store_true",
        help="List genres with no files assigned"
    )

    cleanup_cmd.add_argument(
        "--purge-empty",
        action="store_true",
        help="Delete genres with no files assigned"
    )

    cleanup_cmd.add_argument(
        "--apply-genres",
        action="store_true",
        help="Apply destructive changes (otherwise preview only)"
    )

    return genres

def handle_genres(args, conn):
    # ----------------------------
    # genres list
    # ----------------------------
    if args.genres_command == "list":
        result = list_genres(conn, args.pattern)

        if getattr(args, "raw", False):
            print(result)
            return

        print(f"{msg(result['key'])} {result['pattern']} ({result['count']})")

        for g in result["data"]:
            print(f"- {g['name']} (files: {g['file_count']})")

    # ----------------------------
    # genres normalize
    # ----------------------------
    elif args.genres_command == "normalize":
        result = normalize_genres(
            conn,
            source_genre_names=args.genres,
            target_genre_name=args.to,
            apply=args.apply_genres,
            clear_previous=args.clear_previous,
        )

        if getattr(args, "raw", False):
            print(result)
            return

        stats = result.get("stats", {})

        print(msg(result["key"]))
        print(f"- target: {stats.get('target_genre')}")
        print(f"- sources: {', '.join(stats.get('source_genres', []))}")
        print(f"- files affected: {stats.get('files_affected', 0)}")
        print(f"- links added: {stats.get('links_added', 0)}")
        print(f"- links removed: {stats.get('links_removed', 0)}")
        print(f"- preview: {stats.get('preview')}")

    elif args.genres_command == "cleanup":
        if args.list_empty:
            result = find_empty_genres(conn)

            print(f"{msg(result['key'])} ({result['count']})")
            for g in result["data"]:
                print(f"- {g['name']}")

        elif args.purge_empty:
            result = purge_empty_genres(
                conn,
                apply=args.apply_genres
            )

            print(msg(result["key"]))
            print(f"- removed: {result['count']}")
            print(f"- preview: {result['preview']}")

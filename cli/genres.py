# cli/genres.py

from backend.genre_service import (
    list_genres,
    find_empty_genres,
    purge_empty_genres,
)

from backend.genre_discovery import discover_genres
from backend.i18n.messages import msg
from backend.genre_service import normalize_genres
from backend.reports.taxonomy_report import write_taxonomy_report
from backend.genre_service import normalize_genres_by_ids


def register_genres_commands(subparsers):
    genres = subparsers.add_parser(
        "genres",
        help=msg("GENRES_CMD_HELP")
    )

    genres_sub = genres.add_subparsers(
        dest="genres_command",
        required=True
    )

    list_cmd = genres_sub.add_parser(
        "list",
        help=msg("GENRES_LIST_HELP")
    )

    list_cmd.add_argument(
        "pattern",
        nargs="?",
        default="*",
        help=msg("GENRES_LIST_PATTERN_HELP")
    )

    discover_cmd = genres_sub.add_parser(
        "discover",
        help=msg("GENRES_DISCOVER_HELP")
    )

    discover_cmd.add_argument(
        "--dry-run",
        action="store_true",
        help=msg("GENRES_DISCOVER_DRY_RUN_HELP")
    )

    discover_cmd.add_argument(
        "--clear-previous",
        action="store_true",
        help=msg("GENRES_DISCOVER_CLEAR_HELP")
    )

    normalize_cmd = genres_sub.add_parser(
        "normalize",
        help=msg("GENRES_NORMALIZE_HELP")
    )

    normalize_cmd.add_argument(
        "genres",
        nargs="+",
        help=msg("GENRES_NORMALIZE_SOURCES_HELP")
    )

    normalize_cmd.add_argument(
        "--to",
        required=True,
        help=msg("GENRES_NORMALIZE_TARGET_HELP")
    )

    normalize_cmd.add_argument(
        "--apply-genres",
        action="store_true",
        help=msg("GENRES_NORMALIZE_APPLY_HELP")
    )

    normalize_cmd.add_argument(
        "--clear-previous",
        action="store_true",
        help=msg("GENRES_NORMALIZE_CLEAR_HELP")
    )

    cleanup_cmd = genres_sub.add_parser(
        "cleanup",
        help=msg("GENRES_CLEANUP_HELP")
    )

    cleanup_cmd.add_argument(
        "--list-empty",
        action="store_true",
        help=msg("GENRES_CLEANUP_LIST_HELP")
    )

    cleanup_cmd.add_argument(
        "--purge-empty",
        action="store_true",
        help=msg("GENRES_CLEANUP_PURGE_HELP")
    )

    cleanup_cmd.add_argument(
        "--apply-genres",
        action="store_true",
        help=msg("GENRES_CLEANUP_APPLY_HELP")
    )

    normalize_cmd.add_argument(
        "--from-ids",
        nargs="+",
        type=int,
        help="Source genre IDs (preferred, unambiguous)"
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
            print(f"- [{g['id']}] {g['name']} (files: {g['file_count']})")


    # ----------------------------
    # genres normalize
    # ----------------------------
    elif args.genres_command == "normalize":
        if args.from_ids:
            # ID-based normalization (future-proof, UI-compatible)
            result = normalize_genres_by_ids(
                conn,
                old_genre_ids=args.from_ids,
                canonical_name=args.to,
                apply=args.apply_genres,
                clear_previous=args.clear_previous,
            )
        else:
            # Backwards-compatible name-based normalization
            result = normalize_genres(
                conn,
                source_genre_names=args.genres,
                target_genre_name=args.to,
                apply=args.apply_genres,
                clear_previous=args.clear_previous,
            )

        if "stats" in result:
            stats = result["stats"]
        else:
            stats = {
                "source_genres": args.from_ids,
                "target_genre": args.to,
                "files_affected": result["files_affected"],
                "links_added": None,
                "links_removed": None,
                "preview": result.get("preview", False),
            }


        report_path, _ = write_taxonomy_report(
            taxonomy="genres",
            operation="normalize",
            preview=stats["preview"],
            parameters={
                "source_genres": stats["source_genres"],
                "target_genre": stats["target_genre"],
                "clear_previous": args.clear_previous,
            },
            summary={
                "files_affected": stats["files_affected"],
                "links_added": stats["links_added"],
                "links_removed": stats["links_removed"],
                "canonical_created": False,
                "canonical_removed": 0,
            },
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
        print(f"- report: {report_path}")


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
    
    elif args.genres_command == "discover":
        stats = discover_genres(
            conn,
            apply=not args.dry_run,
            clear_previous=args.clear_previous,
        )

        report_path, _ = write_taxonomy_report(
            taxonomy="genres",
            operation="discover",
            preview=args.dry_run,
            parameters={
                "clear_previous": args.clear_previous,
            },
            summary=stats,
        )

        print(msg("GENRE_DISCOVERY_COMPLETE"))
        for k, v in stats.items():
            print(f"- {k}: {v}")
        print(f"- report: {report_path}")


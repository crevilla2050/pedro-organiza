import argparse
import json
from pathlib import Path

from backend.export_preview import build_preview


def cmd_export_preview(args):
    preset_path = Path(args.preset)

    if not preset_path.exists():
        print(f"Preset not found: {preset_path}")
        return 1

    with open(preset_path, "r", encoding="utf-8") as f:
        preset = json.load(f)

    preview = build_preview(preset, args.db)

    # ---------- JSON output ----------
    if args.json:
        print(json.dumps(preview, indent=2))
        return 0

    # ---------- Human summary ----------
    summary = preview["summary"]

    print("\n📦 Export Preview")
    print("────────────────────────────")
    print(f"Preset:        {summary.get('preset_name')}")
    print(f"Target root:   {summary.get('target_root')}")
    print(f"Files:         {summary.get('total_files')}")
    print(f"Total size:    {summary.get('total_size_bytes'):,} bytes")
    print(f"Conflicts:     {summary.get('conflict_count')}")
    print(f"Preview hash:  {preview.get('preview_hash')}")
    print()

    # Optional list preview
    if args.limit > 0:
        print("Sample files:")
        for item in preview["items"][: args.limit]:
            print(f"  {item['destination']}")

    return 0


def register_export_subparser(subparsers):
    export_parser = subparsers.add_parser(
        "export",
        help="Export operations"
    )

    export_sub = export_parser.add_subparsers(dest="export_cmd")

    # ---------- preview ----------
    preview_parser = export_sub.add_parser(
        "preview",
        help="Preview export preset deterministically"
    )

    preview_parser.add_argument(
        "preset",
        help="Path to preset JSON"
    )

    preview_parser.add_argument(
        "--db",
        required=True,
        help="SQLite database path"
    )

    preview_parser.add_argument(
        "--json",
        action="store_true",
        help="Output full JSON preview"
    )

    preview_parser.add_argument(
        "--limit",
        type=int,
        default=5,
        help="Show first N files (default 5)"
    )

    preview_parser.set_defaults(func=cmd_export_preview)
# backend/create_export_preset.py

import uuid
import argparse
import json
import os
import sys

from backend.export_preset_schema import ExportPreset, ExportLayout, ExportFilters, ExportOptions

def main():
    parser = argparse.ArgumentParser(
        description="Pedro Organiza — Create export preset"
    )

    parser.add_argument("--name", required=True, help="Preset name")
    parser.add_argument("--target", required=True, help="Target root directory for export")
    parser.add_argument("--layout", required=True, help="Layout pattern, e.g. '{artist}/{album}/{track:02d} - {title}'")
    parser.add_argument("--out", required=True, help="Output preset JSON path")

    # Optional flags
    parser.add_argument("--copy-art", choices=["yes", "no"], default="yes")
    parser.add_argument("--allow-delete", choices=["yes", "no"], default="no")
    parser.add_argument("--incremental", choices=["yes", "no"], default="yes")
    parser.add_argument("--include-artist", action="append", default=[],
                    help="Include only files by this artist (can repeat)")

    parser.add_argument("--exclude-artist", action="append", default=[],
                        help="Exclude files by this artist (can repeat)")

    parser.add_argument("--include-album", action="append", default=[],
                        help="Include only files from this album (can repeat)")


    args = parser.parse_args()

    # ---------- Build preset ----------
    preset = ExportPreset(
        preset_id=str(uuid.uuid4()),
        name=args.name,
        target_root=os.path.abspath(args.target),
        layout=ExportLayout(
            pattern=args.layout
        ),
        filters=ExportFilters(),
        options=ExportOptions(
            copy_album_art=(args.copy_art == "yes"),
            allow_delete=(args.allow_delete == "yes"),
            incremental=(args.incremental == "yes"),
        )
    )

    out_path = os.path.abspath(args.out)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(preset.dict(), f, indent=2)

    print(f"OK: Preset written to {out_path}")


if __name__ == "__main__":
    main()

# backend/export_plan_builder.py
import argparse
import json
import os
import sys

from backend.export_plan_schema import (
    ExportPlan,
    ExportPlanSummary,
    ExportAction,
    OrphanDirectory,
)
from backend.export_preset_schema import ExportPreset
from datetime import datetime
from pathlib import Path
import sqlite3
import uuid

from backend.export_preset_schema import ExportPreset
from backend.export_plan_schema import ExportWarning

def build_export_plan(
    preset: ExportPreset,
    *,
    source_root: str,
    library_root: str,
    database_path: str,
    dry_run: bool = True,
) -> ExportPlan:
    """
    Build a deterministic ExportPlan.

    NO filesystem mutation.
    NO copying.
    NO deleting.

    Only compute actions.
    """

    plan_id = str(uuid.uuid4())

    summary = ExportPlanSummary()

    plan = ExportPlan(
        plan_id=plan_id,
        preset_id=preset.preset_id,
        target_root=preset.target_root,
        dry_run=dry_run,

        source_root=source_root,
        library_root=library_root,
        database_path=database_path,

        summary=summary,
        actions=[],
        orphan_directories=[],
        warnings=[],
        errors=[],

        requires_confirmation=True,
        allow_execute=False,
    )

    # =========================
    # 1. Load files from DB
    # =========================

    conn = sqlite3.connect(database_path)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    # Base query — you will extend this with preset filters later
    rows = c.execute("""
        SELECT
            id,
            original_path,
            recommended_path,
            sha256,
            size_bytes,
            lifecycle_state,
            mark_delete
        FROM files
    """).fetchall()

    conn.close()

    # =========================
    # 2. Build desired state
    # =========================

    desired_files = {}

    for row in rows:
        file_id = row["id"]
        src_path = row["original_path"]
        dst_path = row["recommended_path"]

        if not dst_path:
            plan.warnings.append(ExportWarning(
                code="EXPORT_WARNING_NO_RECOMMENDED_PATH",
                file_id=file_id,
            ))
            summary.warnings += 1
            continue

        desired_files[dst_path] = {
            "file_id": file_id,
            "src_path": src_path,
            "sha256": row["sha256"],
            "size": row["size_bytes"],
            "mark_delete": row["mark_delete"],
        }

    summary.files_total = len(desired_files)

    # =========================
    # 3. Scan target filesystem
    # =========================

    target_root = Path(preset.target_root)

    existing_files = {}

    if target_root.exists():
        for p in target_root.rglob("*"):
            if p.is_file():
                rel = str(p.relative_to(target_root))
                existing_files[rel] = {
                    "size": p.stat().st_size,
                    # sha256 optional later (expensive)
                }

    # =========================
    # 4. Diff: desired vs existing
    # =========================

    # A. Files to copy / update / skip

    for rel_dst, info in desired_files.items():
        src = info["src_path"]
        dst = os.path.join(preset.target_root, rel_dst)

        if rel_dst not in existing_files:
            # New file → copy
            plan.actions.append(ExportAction(
                action="copy",
                file_id=info["file_id"],
                src_path=src,
                dst_path=dst,
                size_bytes=info["size"],
            ))
            summary.to_copy += 1
            summary.estimated_bytes += info["size"]
            continue

        # Exists → check if identical
        existing = existing_files[rel_dst]

        if existing["size"] == info["size"]:
            # For now: size match = skip
            plan.actions.append(ExportAction(
                action="skip",
                file_id=info["file_id"],
                src_path=src,
                dst_path=dst,
                reason="EXPORT_REASON_SIZE_MATCH",
            ))
            summary.to_skip += 1
        else:
            # Different → update
            plan.actions.append(ExportAction(
                action="update",
                file_id=info["file_id"],
                src_path=src,
                dst_path=dst,
                size_bytes=info["size"],
            ))
            summary.to_update += 1
            summary.estimated_bytes += info["size"]

    # B. Orphan detection (files in target not in desired)

    desired_set = set(desired_files.keys())

    orphan_files = []

    for rel_dst in existing_files.keys():
        if rel_dst not in desired_set:
            orphan_files.append(rel_dst)
            plan.actions.append(ExportAction(
                action="delete",
                src_path=os.path.join(preset.target_root, rel_dst),
                reason="orphan-file",
            ))
            summary.to_delete += 1

    # =========================
    # 5. Orphan directories
    # =========================

    # Build directory usage map
    used_dirs = set()

    for rel in desired_set:
        d = os.path.dirname(rel)
        while d:
            used_dirs.add(d)
            d = os.path.dirname(d)

    orphan_dirs = []

    if target_root.exists():
        for d in sorted(target_root.rglob("*"), reverse=True):
            if not d.is_dir():
                continue

            rel = str(d.relative_to(target_root))

            if rel not in used_dirs:
                # Check contents
                files = list(d.iterdir())
                contains_only_art = all(
                    f.suffix.lower() in (".jpg", ".jpeg", ".png")
                    for f in files if f.is_file()
                )

                orphan_dirs.append(OrphanDirectory(
                    path=str(d),
                    will_be_empty=True,
                    contains_only_art=contains_only_art,
                ))
                summary.dirs_to_delete += 1

    plan.orphan_directories = orphan_dirs

    # =========================
    # 6. Finalize summary
    # =========================

    summary.dirs_to_create = len({
        os.path.dirname(a.dst_path)
        for a in plan.actions
        if a.action in ("copy", "update") and a.dst_path
    })

    # Safety gate: no execution allowed yet
    plan.allow_execute = False

    return plan

def main():
    parser = argparse.ArgumentParser(
        description="Pedro Organiza — Build export plan from preset"
    )

    parser.add_argument("--preset", required=True, help="Path to export preset JSON")
    parser.add_argument("--db", required=True, help="Path to Pedro database")
    parser.add_argument("--src", required=True, help="Source music root")
    parser.add_argument("--lib", required=True, help="Canonical library root")
    parser.add_argument("--out", required=True, help="Output export plan JSON file")

    args = parser.parse_args()

    # ---------- Sanity checks ----------
    if not os.path.exists(args.preset):
        print(f"ERROR: Preset not found: {args.preset}", file=sys.stderr)
        sys.exit(1)

    if not os.path.exists(args.db):
        print(f"ERROR: Database not found: {args.db}", file=sys.stderr)
        sys.exit(1)

    if not os.path.exists(args.src):
        print(f"ERROR: Source not found: {args.src}", file=sys.stderr)
        sys.exit(1)

    if not os.path.exists(args.lib):
        print(f"ERROR: Library not found: {args.lib}", file=sys.stderr)
        sys.exit(1)

    # ---------- Load preset ----------
    try:
        preset = ExportPreset.parse_file(args.preset)
    except Exception as e:
        print("ERROR: Invalid preset file:", file=sys.stderr)
        print(str(e), file=sys.stderr)
        sys.exit(1)

    # ---------- Build plan ----------
    try:
        plan = build_export_plan(
            preset=preset,                     # 👈 object, not path
            source_root=args.src,              # 👈 matches signature
            library_root=args.lib,             # 👈 matches signature
            database_path=args.db,             # 👈 matches signature
            dry_run=True,
        )
    except Exception as e:
        print("ERROR while building export plan:", file=sys.stderr)
        print(str(e), file=sys.stderr)
        sys.exit(2)

    # ---------- Write output ----------
    out_path = os.path.abspath(args.out)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(plan.model_dump(), f, indent=2)

    print(f"OK: Export plan written to {out_path}")


if __name__ == "__main__":
    main()

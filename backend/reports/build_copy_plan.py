from pathlib import Path
from datetime import datetime, timezone
from backend.reports.copy_plan import CopyPlan, CopyPlanItem, PlanSource
from backend.reports.validate_copy_plan import validate_copy_plan
import hashlib


def build_copy_plan(
    conn,
    file_rows,
    destination_root: str,
    source_db_path: str,
    query_signature: str,
) -> CopyPlan:
    """
    Build a CopyPlan from resolved DB rows.
    Does NOT touch filesystem.
    """

    items = []

    for row in file_rows:
        # Required DB columns
        file_id = row["id"]
        src = row["original_path"]
        dst = row["recommended_path"]

        if not dst:
            raise RuntimeError(
                f"File {file_id} has no recommended_path"
            )

        # dst MUST be relative
        dst_rel = Path(dst)
        if dst_rel.is_absolute():
            raise RuntimeError(
                f"recommended_path must be relative (file_id={file_id})"
            )

        items.append(
            CopyPlanItem(
                file_id=file_id,
                src=src,
                dst=str(dst_rel),
                size=row["size_bytes"],
            )
        )

    plan = CopyPlan(
        plan_version=1,
        operation="apply-copy",
        created_at=datetime.now(timezone.utc).isoformat(),

        source=PlanSource(
            type="database",
            db_path=source_db_path,
            query_hash=query_signature,
        ),

        destination_root=destination_root,
        items=items,
    )

    validate_copy_plan(plan)
    return plan

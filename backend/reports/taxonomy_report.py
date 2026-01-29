# backend/reports/taxonomy_report.py

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from platformdirs import user_config_dir


def utcnow():
    return datetime.now(timezone.utc).isoformat()


def generate_run_id():
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")


def taxonomy_report_dir(taxonomy: str):
    base = Path(user_config_dir("pedro")) / "reports" / "taxonomy" / taxonomy
    base.mkdir(parents=True, exist_ok=True)
    return base


def write_taxonomy_report(
    taxonomy: str,
    operation: str,
    preview: bool,
    parameters: dict,
    summary: dict,
    changes: dict | None = None,
    status: str = "ok",
    warnings: list | None = None,
    errors: list | None = None,
):
    run_id = generate_run_id()
    started_at = utcnow()

    report = {
        "version": 1,
        "taxonomy": taxonomy,
        "operation": operation,
        "run": {
            "run_id": run_id,
            "started_at": started_at,
            "finished_at": started_at,
            "preview": preview,
        },
        "parameters": parameters,
        "summary": summary,
        "changes": changes or {},
        "status": status,
        "warnings": warnings or [],
        "errors": errors or [],
    }

    path = taxonomy_report_dir(taxonomy) / f"{operation}_{run_id}.json"

    with open(path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    return str(path), report

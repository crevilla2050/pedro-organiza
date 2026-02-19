# backend/doctor/reporting.py

from __future__ import annotations
from pathlib import Path
from datetime import datetime
import json
import os


def get_pedro_config_dir() -> Path:
    """
    Resolve Pedro config dir cross-platform.
    Linux/macOS: ~/.config/pedro
    Windows: %APPDATA%/pedro
    """
    if os.name == "nt":
        base = Path(os.getenv("APPDATA", Path.home()))
        return base / "pedro"
    return Path.home() / ".config" / "pedro"


def get_doctor_reports_dir() -> Path:
    return get_pedro_config_dir() / "reports" / "doctor"


def build_timestamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def build_default_report_path() -> Path:
    reports_dir = get_doctor_reports_dir()
    reports_dir.mkdir(parents=True, exist_ok=True)
    filename = f"doctor_{build_timestamp()}.json"
    return reports_dir / filename


def write_report(payload: dict, output_path: str | None = None) -> Path:
    """
    Write doctor report JSON.
    If output_path provided, use it.
    Otherwise use default timestamped path.
    """
    if output_path:
        path = Path(output_path).expanduser()
        path.parent.mkdir(parents=True, exist_ok=True)
    else:
        path = build_default_report_path()

    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    return path

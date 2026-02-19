# backend/doctor/runner.py

"""
Doctor runner.

Loads all doctor checks and executes them.
This is the engine behind `pedro doctor`.
"""

import pkgutil
import importlib
import sqlite3
from datetime import datetime
from typing import List

from backend.doctor.registry import list_checks, run_checks
from backend.doctor.doctor_types import DoctorResult


# ============================================================
# Load all checks dynamically
# ============================================================

def _load_all_checks():
    """
    Import every module inside backend.doctor.checks

    This triggers register_check(...) calls.
    """
    import backend.doctor.checks as checks_pkg

    for _, module_name, _ in pkgutil.iter_modules(checks_pkg.__path__):
        importlib.import_module(f"{checks_pkg.__name__}.{module_name}")


# ============================================================
# Public runner API
# ============================================================

def run_doctor(conn: sqlite3.Connection) -> List[DoctorResult]:
    """
    Execute all registered doctor checks.
    """
    _load_all_checks()
    names = list_checks()
    return run_checks(conn, names)
    # return run_checks(conn, QUICK_CHECKS)

# ============================================================
# Payload builder
# ============================================================

def build_doctor_payload(results):
    issues = []
    checks = []

    for r in results:
        checks.append({
            "check": r.check,
            "ok": r.ok,
            "meta": getattr(r, "meta", {})
        })

        for issue in getattr(r, "issues", []):
            issues.append({
                "check": r.check,
                "code": issue.code,
                "severity": issue.severity,
                "message": issue.message,
                "fix_hint": getattr(issue, "fix_hint", None),
                "details": getattr(issue, "details", None),
            })

    summary = {
        "total_checks": len(results),
        "failed_checks": sum(1 for r in results if not r.ok),
        "total_issues": len(issues),
    }

    return {
        "timestamp": datetime.now().isoformat(),
        "summary": summary,
        "checks": checks,
        "issues": issues,
    }

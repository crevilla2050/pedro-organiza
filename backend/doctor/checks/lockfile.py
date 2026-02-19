"""
Doctor check: Lock file integrity

Detects stale or active Pedro lock files.
"""

import os
import time
from ..doctor_types import DoctorResult, DoctorIssue

STALE_SECONDS = 60 * 60 * 24  # 24 hours or 1 day


def check_lock_file(conn, config=None):
    if config is None:
        config = {}
    lock_path = config.get("lock_file")

    # ----------------------------------------
    # No lock configured → OK
    # ----------------------------------------
    if not lock_path:
        return DoctorResult(
            "lock_file",
            True,
            [],
            {"configured": False},
        )

    # ----------------------------------------
    # No lock present → OK
    # ----------------------------------------
    if not os.path.exists(lock_path):
        return DoctorResult(
            "lock_file",
            True,
            [],
            {"configured": True, "present": False},
        )

    # ----------------------------------------
    # Lock exists → inspect
    # ----------------------------------------
    try:
        mtime = os.path.getmtime(lock_path)
        age_seconds = time.time() - mtime
    except Exception as e:
        return DoctorResult(
            "lock_file",
            False,
            [
                DoctorIssue(
                    code="LOCK_UNREADABLE",
                    severity="warn",
                    message="Lock file exists but cannot be inspected",
                    fix_hint="Consider deleting the lock file manually",
                    details={"error": str(e)},
                )
            ],
            {"path": lock_path},
        )

    # ----------------------------------------
    # Stale lock detection
    # ----------------------------------------
    is_stale = age_seconds > STALE_SECONDS

    if is_stale:
        issues = [
            DoctorIssue(
                code="STALE_LOCK",
                severity="warn",
                message="Stale Pedro lock file detected",
                fix_hint="Safe to remove. Run: pedro doctor --autofix",
                autofix_tier="safe",
                details={
                    "path": lock_path,
                    "age_seconds": int(age_seconds),
                },
            )
        ]

        return DoctorResult(
            "lock_file",
            False,
            issues,
            {
                "path": lock_path,
                "stale": True,
                "age_seconds": int(age_seconds),
            },
        )

    # ----------------------------------------
    # Active lock (recent)
    # ----------------------------------------
    issues = [
        DoctorIssue(
            code="LOCK_PRESENT",
            severity="warn",
            message="Pedro lock file exists (possible running or crashed process)",
            fix_hint="Ensure no Pedro process is running before deleting",
            details={
                "path": lock_path,
                "age_seconds": int(age_seconds),
            },
        )
    ]

    return DoctorResult(
        "lock_file",
        False,
        issues,
        {
            "path": lock_path,
            "stale": False,
            "age_seconds": int(age_seconds),
        },
    )


# ----------------------------------------
# Registration (safe now)
# ----------------------------------------
from ..registry import register_check
register_check("lockfile", check_lock_file)


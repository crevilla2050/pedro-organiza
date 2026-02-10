from platformdirs import user_config_dir
from pathlib import Path
import os

APP_NAME = "pedro"
OLD_APP_NAME = "pedro-organiza"
BASE_CONFIG_DIR = user_config_dir(APP_NAME)

def _migrate_runtime_dir():
    """
    One-time migration from ~/.config/pedro-organiza → ~/.config/pedro

    Safe because:
    - rename is atomic
    - occurs before paths are exported
    - avoids dual runtime directories forever
    """

    new_dir = Path(user_config_dir(APP_NAME))
    old_dir = Path(user_config_dir(OLD_APP_NAME))

    # Case 1 — new already exists → nothing to do
    if new_dir.exists():
        return new_dir

    # Case 2 — old exists → migrate
    if old_dir.exists():
        try:
            old_dir.rename(new_dir)
        except Exception as e:
            raise RuntimeError(
                f"FAILED_RUNTIME_MIGRATION: could not rename "
                f"{old_dir} → {new_dir}: {e}"
            )

        return new_dir

    # Case 3 — fresh install
    new_dir.mkdir(parents=True, exist_ok=True)
    return new_dir


BASE_CONFIG_DIR = _migrate_runtime_dir()

def ensure_dir(path):
    Path(path).mkdir(parents=True, exist_ok=True)
    return path

# ---- Canonical paths ----

LAST_RUN_PLAN_PATH = os.path.join(
    ensure_dir(BASE_CONFIG_DIR),
    "last_run_plan.json"
)

LAST_DRY_RUN_REPORT_PATH = os.path.join(
    ensure_dir(BASE_CONFIG_DIR),
    "last_dry_run_report.json"
)

ACTIVE_DB_PATH = os.path.join(
    ensure_dir(BASE_CONFIG_DIR),
    "active_db.json"
)

APPLY_REPORT_DIR = ensure_dir(
    os.path.join(BASE_CONFIG_DIR, "apply_reports")
)

# OS-safe temp file
SCAN_LOCK_PATH = os.path.join(
    ensure_dir(os.path.join(BASE_CONFIG_DIR, "locks")),
    "scan.lock"
)

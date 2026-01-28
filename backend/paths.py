from platformdirs import user_config_dir
import os

APP_NAME = "pedro-organiza"

BASE_CONFIG_DIR = user_config_dir(APP_NAME)

def ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)
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

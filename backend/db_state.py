# backend/db_state.py

import json
from pathlib import Path
from platformdirs import user_config_dir

APP_NAME = "pedro"
CONFIG_DIR = Path(user_config_dir(APP_NAME))
ACTIVE_DB_FILE = CONFIG_DIR / "active_db.json"


def set_active_db(db_path: str):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(ACTIVE_DB_FILE, "w", encoding="utf-8") as f:
        json.dump({"db_path": db_path}, f)


def get_active_db() -> str | None:
    if not ACTIVE_DB_FILE.exists():
        return None
    with open(ACTIVE_DB_FILE, "r", encoding="utf-8") as f:
        return json.load(f).get("db_path")


def clear_active_db():
    if ACTIVE_DB_FILE.exists():
        ACTIVE_DB_FILE.unlink()

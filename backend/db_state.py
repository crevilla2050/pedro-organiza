# backend/db_state.py

import json
from pathlib import Path
from sys import path
from backend.paths import BASE_CONFIG_DIR

CONFIG_DIR = Path(BASE_CONFIG_DIR)
ACTIVE_DB_FILE = CONFIG_DIR / "active_db.json"


def set_active_db(db_path: str):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    # Normalize to absolute path (critical)
    db_path = str(Path(db_path).expanduser().resolve())

    with open(ACTIVE_DB_FILE, "w", encoding="utf-8") as f:
        json.dump({"db_path": db_path}, f)

    # Backward compatibility: update .env
    from dotenv import set_key
    env_path = Path(".env")
    set_key(env_path, "MUSIC_DB", db_path)


def get_active_db() -> str | None:
    if not ACTIVE_DB_FILE.exists():
        return None
    with open(ACTIVE_DB_FILE, "r", encoding="utf-8") as f:
        return json.load(f).get("db_path")


def clear_active_db():
    if ACTIVE_DB_FILE.exists():
        ACTIVE_DB_FILE.unlink()

import json
import os
from backend.paths import ACTIVE_DB_PATH

def set_active_db(db_path: str):
    os.makedirs(os.path.dirname(ACTIVE_DB_PATH), exist_ok=True)
    with open(ACTIVE_DB_PATH, "w", encoding="utf-8") as f:
        json.dump({"db_path": db_path}, f)

def get_active_db():
    if not os.path.exists(ACTIVE_DB_PATH):
        return None

    with open(ACTIVE_DB_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    return data.get("db_path")

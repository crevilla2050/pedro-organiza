import os
import json
from datetime import datetime, timezone

LAST_RUN_PLAN_PATH = os.path.expanduser("~/.config/pedro/last_run_plan.json")

def utcnow():
    return datetime.now(timezone.utc).isoformat()

def save_last_run_plan(plan: dict):
    os.makedirs(os.path.dirname(LAST_RUN_PLAN_PATH), exist_ok=True)

    data = {
        "saved_at": utcnow(),
        "plan_version": 1,
        "plan": plan,
    }

    with open(LAST_RUN_PLAN_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def load_last_run_plan():
    if not os.path.exists(LAST_RUN_PLAN_PATH):
        return None

    with open(LAST_RUN_PLAN_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

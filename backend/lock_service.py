from pathlib import Path
import json
import os
from datetime import datetime, timezone

from backend.paths import BASE_CONFIG_DIR


LOCK_DIR = Path(BASE_CONFIG_DIR) / "locks"
LOCK_DIR.mkdir(parents=True, exist_ok=True)


def _utc_now():
    return datetime.now(timezone.utc).isoformat()


class LockError(RuntimeError):
    pass


def acquire_lock(name: str):
    """
    Acquire a named lock.

    Raises LockError if the lock already exists.
    """

    lock_path = LOCK_DIR / f"{name}.lock"

    if lock_path.exists():
        try:
            data = json.loads(lock_path.read_text())
            created = data.get("created_at", "unknown")
            pid = data.get("pid", "unknown")
        except Exception:
            created = "unknown"
            pid = "unknown"

        raise LockError(
            f"{name} already running.\n"
            f"Lock created_at={created}, pid={pid}\n"
            f"If you are sure this is stale, remove:\n{lock_path}"
        )

    payload = {
        "created_at": _utc_now(),
        "pid": os.getpid(),
        "operation": name,
    }

    lock_path.write_text(json.dumps(payload, indent=2))

    return lock_path


def release_lock(lock_path: Path):
    """
    Always call from a finally block.
    """

    try:
        if lock_path.exists():
            lock_path.unlink()
    except Exception:
        # Never crash while releasing a lock.
        pass

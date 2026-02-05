"""
config_service.py

Pedro Organiza — Configuration Backbone

Single source of truth for reading Pedro configuration.

RULE:
No other module should read config.json directly.
Always import from config_service.

Design goals:
- deterministic
- safe defaults
- expanduser support (~)
- future schema migrations
- i18n-ready errors
"""

from pathlib import Path
import json

# --------------------------------------------------
# PATHS
# --------------------------------------------------

ROOT_DIR = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT_DIR / "backend" / "config.json"

# --------------------------------------------------
# DEFAULT CONFIG (schema seed)
# --------------------------------------------------

DEFAULT_CONFIG = {
    "language": "en",
    "versions": {
        "normalization": "v1.0",
        "signals": "v1.0",
        "grouping": "v1.0"
    },
    "ui": {
        "translate": True
    },
    "paths": {
        "quarantine_path": "~/PedroQuarantine"
    }
}

# --------------------------------------------------
# INTERNAL HELPERS
# --------------------------------------------------

def _deep_merge(default: dict, user: dict) -> dict:
    """
    Recursively merge user config over defaults.
    Ensures missing keys never crash Pedro.
    """
    result = default.copy()

    for key, value in user.items():
        if (
            key in result
            and isinstance(result[key], dict)
            and isinstance(value, dict)
        ):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value

    return result


# --------------------------------------------------
# PUBLIC API
# --------------------------------------------------

def load_config() -> dict:
    """
    Load config.json safely.

    If missing → create default automatically.
    If partially missing → merge with defaults.
    """

    if not CONFIG_PATH.exists():
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG

    try:
        user_cfg = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except Exception as e:
        raise RuntimeError(f"CONFIG_INVALID: {e}")

    return _deep_merge(DEFAULT_CONFIG, user_cfg)


def save_config(cfg: dict):
    """
    Persist config safely.
    """
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(
        json.dumps(cfg, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )


def get_config_path():
    return CONFIG_PATH

# --------------------------------------------------
# HIGH LEVEL GETTERS (preferred usage)
# --------------------------------------------------

def get_language() -> str:
    return load_config()["language"]


def get_quarantine_path() -> Path:
    path = load_config()["paths"]["quarantine_path"]
    return Path(path).expanduser().resolve()


def ensure_quarantine_exists() -> Path:
    """
    Guarantees quarantine directory exists.
    Safe to call before execution layer runs.
    """
    q = get_quarantine_path()
    q.mkdir(parents=True, exist_ok=True)
    return q


# --------------------------------------------------
# FUTURE: MIGRATIONS HOOK
# --------------------------------------------------

def config_version() -> dict:
    """
    Placeholder for future schema migrations,
    this in 0.9+.
    """
    return load_config().get("versions", {})
# --------------------------------------------------
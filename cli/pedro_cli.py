#!/usr/bin/env python3
"""
Pedro Organiza — CLI Wrapper with i18n support
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

from backend.config_service import load_config, save_config

# ---------------- PATHS ----------------

ROOT_DIR = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT_DIR / "backend" / "config.json"
I18N_DIR = ROOT_DIR / "music-ui" / "src" / "i18n"


# ---------------- DEFAULT CONFIG ----------------

def default_config():
    return {
        "language": "en",
        "versions": {
            "normalization": "v1.0",
            "signals": "v1.0",
            "grouping": "v1.0",
            "config_version": "1.0",
        },
        "ui": {
            "translate": True
        },
        "paths": {
            "quarantine_path": "~/PedroQuarantine"
        }
    }


# ---------------- I18N ----------------

def available_languages():
    return {p.stem for p in I18N_DIR.glob("*.json")}


def load_translations(lang: str):
    path = I18N_DIR / f"{lang}.json"
    if not path.exists():
        raise FileNotFoundError(lang)
    return json.loads(path.read_text(encoding="utf-8"))


def resolve_language(cli_lang, config, langs):
    if cli_lang:
        if cli_lang in langs:
            return cli_lang, None
        return "en", f"Unknown language '{cli_lang}', falling back to English."

    if config:
        cfg_lang = config.get("language", "en")
        if cfg_lang in langs:
            return cfg_lang, None
        return "en", f"Unknown language '{cfg_lang}' in config, falling back to English."

    return "en", None


def render_message(obj, translations):
    if not isinstance(obj, dict):
        return str(obj)

    key = obj.get("key")
    params = obj.get("params", {})

    if not key:
        return json.dumps(obj, ensure_ascii=False)

    template = translations.get(key, key)

    try:
        return template.format(**params)
    except Exception:
        return template + f" {params}"


# ---------------- EXECUTION ----------------

def run_script(script_path, script_args, translations, raw=False):
    cmd = [sys.executable, script_path] + script_args

    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    for line in proc.stdout:
        line = line.strip()
        if not line:
            continue

        if raw:
            print(line)
            continue

        try:
            obj = json.loads(line.replace("'", '"'))
            print(render_message(obj, translations))
        except Exception:
            print(line)

    proc.wait()
    return proc.returncode


# ---------------- CLI ----------------

def main():
    parser = argparse.ArgumentParser(description="Pedro Organiza CLI")

    parser.add_argument("--lang", help="Override language (en, es, de)")
    parser.add_argument("--raw", action="store_true", help="Do not translate output")

    sub = parser.add_subparsers(dest="command")

    # ---------------- TEST ----------------
    p_test = sub.add_parser("test", help="Run Pedro test corpus")
    p_test.add_argument("--verbose", action="store_true")
    p_test.add_argument("--only")
    p_test.add_argument("--fail-fast", action="store_true")

    # ---------------- INIT ----------------
    p_init = sub.add_parser("init", help="Initialize Pedro config")
    p_init.add_argument("--lang")
    p_init.add_argument("--force", action="store_true")

    # ---------------- STATUS ----------------
    sub.add_parser("status", help="Show Pedro status")

    # ---------------- RUN ----------------
    p_run = sub.add_parser("run", help="Run a backend script")
    p_run.add_argument("script")
    p_run.add_argument("script_args", nargs=argparse.REMAINDER)

    # =====================================================
    # ⭐ CONFIG COMMAND TREE (NEW — Pedro 0.7)
    # =====================================================

    p_config = sub.add_parser("config", help="Manage Pedro configuration")
    config_sub = p_config.add_subparsers(dest="config_cmd")

    config_sub.add_parser("show", help="Show current config")

    p_set = config_sub.add_parser("set", help="Set config value")
    p_set.add_argument("key", help="Dot path (example: paths.quarantine_path)")
    p_set.add_argument("value")

    args = parser.parse_args()

    langs = available_languages()
    config = load_config()

    # ---------------- INIT ----------------

    if args.command == "init":
        if CONFIG_PATH.exists() and not args.force:
            print("Config already exists. Use --force to overwrite.")
            sys.exit(1)

        cfg = default_config()
        if args.lang:
            cfg["language"] = args.lang

        save_config(cfg)

        print(f"Config initialized at {CONFIG_PATH}")
        sys.exit(0)

    # ---------------- LANGUAGE ----------------

    lang, warning = resolve_language(args.lang, config, langs)
    if warning:
        print(f"[WARN] {warning}")

    try:
        translations = load_translations(lang)
    except FileNotFoundError:
        print("[WARN] Failed to load translations, using raw output.")
        translations = {}
        args.raw = True

    # ---------------- STATUS ----------------

    if args.command == "status":
        print("Pedro Organiza")
        print("--------------")
        print(f"Language:     {lang}")
        print(f"Config file:  {CONFIG_PATH if CONFIG_PATH.exists() else 'missing'}")
        sys.exit(0)

    # ---------------- TEST ----------------

    if args.command == "test":
        from cli.test_runner import run_tests

        exit_code = run_tests(
            verbose=args.verbose,
            only=args.only,
            fail_fast=args.fail_fast,
        )
        sys.exit(exit_code)

    # ---------------- CONFIG ----------------

    if args.command == "config":

        cfg = load_config()

        if args.config_cmd == "show":
            print(json.dumps(cfg, indent=2, ensure_ascii=False))
            sys.exit(0)

        if args.config_cmd == "set":

            keys = args.key.split(".")
            ref = cfg

            for k in keys[:-1]:
                ref = ref.setdefault(k, {})

            value = args.value

            # small type coercion
            if value.lower() in ("true", "false"):
                value = value.lower() == "true"

            ref[keys[-1]] = value

            save_config(cfg)

            print(f"Updated {args.key}")
            sys.exit(0)

        p_config.print_help()
        sys.exit(0)

    # ---------------- RUN ----------------

    if args.command == "run":
        exit_code = run_script(
            args.script,
            args.script_args,
            translations,
            raw=args.raw
        )
        sys.exit(exit_code)

    parser.print_help()


if __name__ == "__main__":
    main()

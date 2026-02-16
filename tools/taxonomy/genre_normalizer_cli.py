#!/usr/bin/env python3
"""
genre_normalizer_cli.py

Interactive CLI for genre normalization.
Fully i18n-compliant (no hardcoded English strings).
"""

import sqlite3
import re
import json
import os
from datetime import datetime, timezone
from pathlib import Path


# ================= I18N =================

LANG = os.getenv("PEDRO_LANG", "en")
I18N_PATH = Path("music-ui/src/i18n") / f"{LANG}.json"

def load_messages():
    if I18N_PATH.exists():
        try:
            with open(I18N_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

_MESSAGES = load_messages()

def msg(key: str, **params) -> str:
    text = _MESSAGES.get(key, key)
    if params:
        try:
            return text.format(**params)
        except Exception:
            return text
    return text


# ================= HELPERS =================

def utcnow():
    return datetime.now(timezone.utc).isoformat()


def normalize_token(token: str) -> str:
    """Normalize raw genre token for matching."""
    return re.sub(r"\s+", " ", token.strip().lower())


def split_genres(raw: str):
    if not raw:
        return []
    return [g.strip() for g in re.split(r"[;,/]", raw) if g.strip()]


# ================= CORE =================

def main(db_path, apply=True):
    conn = None
    try:
        print(msg("GENRE_NORMALIZATION_STARTED"))
        print(msg("DATABASE_PATH", path=db_path))
        print(msg("GENRE_NORMALIZATION_MODE", mode="APPLY" if apply else "PREVIEW"))
        print()

        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()

        # --------------------------------------------------
        # Collect distinct raw genre tokens
        # --------------------------------------------------
        raw_tokens = set()

        for row in c.execute(
            "SELECT DISTINCT genre FROM files WHERE genre IS NOT NULL"
        ):
            for token in split_genres(row["genre"]):
                raw_tokens.add(token)

        # --------------------------------------------------
        # Load existing mappings
        # --------------------------------------------------
        mapped = {
            r["normalized_token"]
            for r in c.execute("SELECT normalized_token FROM genre_mappings")
        }

        unmapped = [
            t for t in sorted(raw_tokens)
            if normalize_token(t) not in mapped
        ]

        if not unmapped:
            print(msg("UNMAPPED_GENRES_COUNT", count=0))
            return

        print(msg("UNMAPPED_GENRES_HEADER"))
        print()

        applied_relations = 0

        for token in unmapped:
            norm = normalize_token(token)

            print(msg("GENRE_TOKEN", token=token))
            choice = input(
                msg("GENRE_CHOICE_PROMPT")
            ).strip().lower()

            if choice == "s":
                print(msg("GENRE_SKIPPED"))
                continue

            if choice == "i":
                if apply:
                    c.execute("""
                        INSERT OR IGNORE INTO genre_mappings (
                            raw_token, normalized_token, genre_id, source, created_at
                        )
                        VALUES (?, ?, NULL, 'user', ?)
                    """, (token, norm, utcnow()))
                print(msg("GENRE_IGNORED"))
                continue

            if choice == "m":
                suggested = token.strip()
                canonical = input(
                    msg(
                        "GENRE_CANONICAL_PROMPT",
                        suggestion=suggested
                    )
                ).strip()

                if not canonical:
                    canonical = suggested

                canon_norm = normalize_token(canonical)

                if apply:
                    c.execute("""
                        INSERT OR IGNORE INTO genres (
                            name, normalized_name, source, created_at
                        )
                        VALUES (?, ?, 'user', ?)
                    """, (canonical, canon_norm, utcnow()))

                    genre_id = c.execute("""
                        SELECT id FROM genres WHERE normalized_name=?
                    """, (canon_norm,)).fetchone()["id"]

                    c.execute("""
                        INSERT OR REPLACE INTO genre_mappings (
                            raw_token, normalized_token, genre_id, source, created_at
                        )
                        VALUES (?, ?, ?, 'user', ?)
                    """, (token, norm, genre_id, utcnow()))

                    applied_relations += 1

                print(msg("GENRE_MAPPED"))

        if apply:
            conn.commit()

        print()
        print(msg("GENRE_APPLY_SUMMARY", count=applied_relations))

    except Exception as e:
        print(msg("GENRE_NORMALIZATION_FAILED", error=str(e)))
        raise
    finally:
        if conn:
            conn.close()


# ================= CLI =================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--db", required=True)
    parser.add_argument(
        "--preview",
        action="store_true",
        help=msg("PREVIEW_CHANGES")
    )

    args = parser.parse_args()

    main(
        db_path=args.db,
        apply=not args.preview
    )

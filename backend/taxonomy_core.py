# backend/taxonomy_core.py

import fnmatch
from datetime import datetime, timezone
import re

# =============================
# helpers
# =============================

def utcnow():
    return datetime.now(timezone.utc).isoformat()

def split_tokens(raw: str):
    """
    Split a free-form taxonomy string into individual tokens.

    Used by genre discovery, tag discovery, and future taxonomies.
    """
    if not raw:
        return []
    return [t.strip() for t in re.split(r"[;,/]", raw) if t.strip()]

def normalize_token(token: str) -> str:
    return " ".join(token.strip().lower().split())


# =============================
# list
# =============================

def list_canonical(conn, spec, pattern="*"):
    """
    List canonical taxonomy values with file usage counts.
    Wildcards supported.
    """

    c = conn.cursor()

    rows = c.execute(f"""
        SELECT
            t.{spec['canonical_id']}   AS id,
            t.{spec['canonical_name']} AS name,
            t.{spec['canonical_norm']} AS norm,
            COUNT(l.{spec['file_link_file_id']}) AS file_count
        FROM {spec['canonical_table']} t
        LEFT JOIN {spec['file_link_table']} l
               ON l.{spec['file_link_taxonomy_id']} = t.{spec['canonical_id']}
        GROUP BY t.{spec['canonical_id']}
        ORDER BY t.{spec['canonical_name']}
    """).fetchall()

    matched = []
    for r in rows:
        if (
            fnmatch.fnmatchcase(r["name"], pattern)
            or fnmatch.fnmatchcase(r["norm"], pattern.lower())
        ):
            matched.append(dict(r))

    return {
        "key": "TAXONOMY_LISTED",
        "pattern": pattern,
        "count": len(matched),
        "data": matched,
    }


# =============================
# ensure canonical
# =============================

def ensure_canonical(conn, spec, name, source="user"):
    """
    Create canonical value if missing.
    Returns canonical_id.
    """

    c = conn.cursor()
    norm = normalize_token(name)

    row = c.execute(
        f"""
        SELECT {spec['canonical_id']}
        FROM {spec['canonical_table']}
        WHERE {spec['canonical_norm']} = ?
        """,
        (norm,),
    ).fetchone()

    if row:
        return {
            "created": False,
            "id": row[0],
        }

    c.execute(
        f"""
        INSERT INTO {spec['canonical_table']}
        ({spec['canonical_name']}, {spec['canonical_norm']}, source, created_at)
        VALUES (?, ?, ?, ?)
        """,
        (name, norm, source, utcnow()),
    )

    return {
        "created": True,
        "id": c.lastrowid,
    }


# =============================
# normalize (many → one)
# =============================

def normalize_canonical(
    conn,
    spec,
    source_names,
    target_name,
    apply=False,
    clear_previous=False,
):
    """
    Normalize multiple canonical values into a target canonical value.
    """

    c = conn.cursor()

    stats = {
        "source_values": source_names,
        "target_value": target_name,
        "files_affected": 0,
        "links_added": 0,
        "links_removed": 0,
        "preview": not apply,
    }

    # ---- resolve target ----
    target = ensure_canonical(conn, spec, target_name)
    target_id = target["id"]

    # ---- resolve sources ----
    placeholders = ",".join("?" for _ in source_names)

    rows = c.execute(
        f"""
        SELECT {spec['canonical_id']}
        FROM {spec['canonical_table']}
        WHERE {spec['canonical_name']} IN ({placeholders})
        """,
        source_names,
    ).fetchall()

    if not rows:
        return {
            "key": "TAXONOMY_NOT_FOUND",
            "stats": stats,
        }

    source_ids = [r[0] for r in rows]

    # ---- affected files ----
    file_rows = c.execute(
        f"""
        SELECT DISTINCT {spec['file_link_file_id']}
        FROM {spec['file_link_table']}
        WHERE {spec['file_link_taxonomy_id']} IN ({",".join("?" for _ in source_ids)})
        """,
        source_ids,
    ).fetchall()

    file_ids = [r[0] for r in file_rows]
    stats["files_affected"] = len(file_ids)

    # ---- apply changes ----
    for file_id in file_ids:

        if clear_previous:
            if apply:
                cur = c.execute(
                    f"""
                    DELETE FROM {spec['file_link_table']}
                    WHERE {spec['file_link_file_id']} = ?
                      AND {spec['file_link_taxonomy_id']} IN ({",".join("?" for _ in source_ids)})
                    """,
                    (file_id, *source_ids),
                )
                stats["links_removed"] += cur.rowcount
            else:
                stats["links_removed"] += len(source_ids)

        if apply:
            c.execute(
                f"""
                INSERT OR IGNORE INTO {spec['file_link_table']}
                ({spec['file_link_file_id']}, {spec['file_link_taxonomy_id']}, source, confidence, created_at)
                VALUES (?, ?, 'normalize', 1.0, ?)
                """,
                (file_id, target_id, utcnow()),
            )
            stats["links_added"] += c.rowcount
        else:
            stats["links_added"] += 1

    if apply:
        conn.commit()

    return {
        "key": "TAXONOMY_NORMALIZED",
        "stats": stats,
    }


# =============================
# cleanup empty
# =============================

def find_empty_canonical(conn, spec):
    c = conn.cursor()

    rows = c.execute(
        f"""
        SELECT t.{spec['canonical_id']} AS id,
               t.{spec['canonical_name']} AS name
        FROM {spec['canonical_table']} t
        LEFT JOIN {spec['file_link_table']} l
               ON l.{spec['file_link_taxonomy_id']} = t.{spec['canonical_id']}
        WHERE l.{spec['file_link_taxonomy_id']} IS NULL
        ORDER BY t.{spec['canonical_name']}
        """
    ).fetchall()

    return {
        "key": "EMPTY_TAXONOMY_FOUND",
        "count": len(rows),
        "data": [dict(r) for r in rows],
    }


def purge_empty_canonical(conn, spec, apply=False):
    c = conn.cursor()

    empty = find_empty_canonical(conn, spec)["data"]
    ids = [r["id"] for r in empty]

    if not apply:
        return {
            "key": "EMPTY_TAXONOMY_PREVIEW",
            "count": len(ids),
            "values": [r["name"] for r in empty],
            "preview": True,
        }

    if ids:
        placeholders = ",".join("?" for _ in ids)
        c.execute(
            f"DELETE FROM {spec['canonical_table']} WHERE {spec['canonical_id']} IN ({placeholders})",
            ids,
        )
        conn.commit()

    return {
        "key": "EMPTY_TAXONOMY_PURGED",
        "count": len(ids),
        "preview": False,
    }

def taxonomy_for_selection(conn, spec, file_ids):
    c = conn.cursor()

    if not file_ids:
        rows = c.execute(
            f"SELECT {spec['canonical_id']} AS id, "
            f"{spec['canonical_name']} AS name "
            f"FROM {spec['canonical_table']} "
            f"ORDER BY {spec['canonical_name']}"
        ).fetchall()

        return {
            "applied": [],
            "partial": [],
            "available": [dict(r) for r in rows],
        }

    placeholders = ",".join("?" for _ in file_ids)

    rows = c.execute(
        f"""
        WITH hits AS (
            SELECT
                l.{spec['file_link_taxonomy_id']} AS taxonomy_id,
                COUNT(DISTINCT l.{spec['file_link_file_id']}) AS hit_count
            FROM {spec['file_link_table']} l
            WHERE l.{spec['file_link_file_id']} IN ({placeholders})
            GROUP BY l.{spec['file_link_taxonomy_id']}
        )
        SELECT
            t.{spec['canonical_id']} AS id,
            t.{spec['canonical_name']} AS name,
            h.hit_count,
            ? AS total
        FROM {spec['canonical_table']} t
        LEFT JOIN hits h ON h.taxonomy_id = t.{spec['canonical_id']}
        ORDER BY t.{spec['canonical_name']}
        """,
        (*file_ids, len(file_ids)),
    ).fetchall()

    applied, partial, available = [], [], []

    for r in rows:
        entry = {"id": r["id"], "name": r["name"]}

        if r["hit_count"] is None:
            available.append(entry)
        elif r["hit_count"] == r["total"]:
            applied.append(entry)
        else:
            partial.append(entry)

    return {
        "applied": applied,
        "partial": partial,
        "available": available,
    }


#!/usr/bin/env python3
"""
api.py

Pedro Organiza — API v1

Stable backend API for:
- file browsing
- enrichment preview
- alias clusters
- side panel selection logic (tags + genres)

Rules:
- No filesystem mutation
- No inference
- No UI logic
- Deterministic behavior only
"""

import os
import sqlite3
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

from tools.new_pedro_tagger import pedro_enrich_file
from backend.alias_engine import clusters_as_records

from backend.tag_service import (
    tags_for_selection,
    apply_tags,
    remove_tags,
)

from backend.genre_service import (
    genres_for_selection,
    apply_genres,
    remove_genres,
)

# ===================== ENV =====================

load_dotenv()

DB_PATH = os.getenv("MUSIC_DB")
if not DB_PATH:
    raise RuntimeError("MUSIC_DB_NOT_SET")

# ===================== APP =====================

app = FastAPI(
    title="Pedro Organiza API",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===================== HELPERS =====================

def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# ===================== MODELS =====================

class FileSummary(BaseModel):
    id: int
    original_path: str
    artist: Optional[str]
    album_artist: Optional[str]
    album: Optional[str]
    title: Optional[str]


class EnrichmentResult(BaseModel):
    success: bool
    confidence: float
    source: str
    notes: Optional[str] = None
    tags: Optional[dict] = None


# ---------- Alias Clusters ----------

class AliasClusterFile(BaseModel):
    id: int
    artist: Optional[str]
    album: Optional[str]
    title: Optional[str]
    original_path: Optional[str]


class AliasCluster(BaseModel):
    cluster_id: int
    size: int
    confidence: Optional[float]
    signals: Dict[str, int]

    canonical_candidate_id: Optional[int] = None
    resolution_status: str = "unresolved"
    user_decision: Optional[Any] = None
    notes: Optional[str] = None
    cluster_tags: List[str] = []

    files: List[AliasClusterFile]


# ---------- Selection / Side Panel ----------

class SelectionPayload(BaseModel):
    entity_type: str
    entity_ids: List[int]


class TagMutationPayload(SelectionPayload):
    tag_ids: List[int]


class GenreMutationPayload(SelectionPayload):
    genre_ids: List[int]

# ===================== ENDPOINTS =====================

@app.get("/files", response_model=List[FileSummary])
def list_files():
    """
    List ALL files (no pagination by design).
    """
    conn = get_db()
    rows = conn.execute("""
        SELECT
            id,
            original_path,
            artist,
            album_artist,
            album,
            title
        FROM files
        ORDER BY id
    """).fetchall()
    conn.close()

    return [FileSummary(**dict(r)) for r in rows]


@app.post("/files/{file_id}/enrich", response_model=EnrichmentResult)
def enrich_file(file_id: int):
    conn = get_db()
    row = conn.execute(
        "SELECT * FROM files WHERE id = ?",
        (file_id,),
    ).fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="FILE_NOT_FOUND")

    result = pedro_enrich_file(
        source_path=row["original_path"],
        artist_hint=row["artist"],
        title_hint=row["title"],
        album_artist_hint=row["album_artist"],
        is_compilation_hint=row["is_compilation"],
    )

    return EnrichmentResult(
        success=result.get("success", False),
        confidence=result.get("confidence", 0.0),
        source=result.get("source", "unknown"),
        notes=result.get("notes"),
        tags=result.get("tags"),
    )

# ===================== ALIAS CLUSTERS =====================

@app.get("/aliases/clusters", response_model=List[AliasCluster])
def list_alias_clusters(
    min_size: int = Query(2, ge=2),
):
    conn = get_db()
    clusters = clusters_as_records(conn, min_size=min_size)
    conn.close()

    results = []
    for idx, cluster in enumerate(clusters, start=1):
        results.append({
            "cluster_id": idx,
            "size": cluster["size"],
            "confidence": cluster.get("confidence"),
            "signals": cluster.get("signals", {}),
            "canonical_candidate_id": None,
            "resolution_status": "unresolved",
            "user_decision": None,
            "notes": None,
            "cluster_tags": [],
            "files": cluster["files"],
        })

    return results

# ===================== SIDE PANEL: TAGS =====================

@app.post("/selection/tags")
def selection_tags(payload: SelectionPayload):
    conn = get_db()
    try:
        return tags_for_selection(
            conn,
            entity_type=payload.entity_type,
            entity_ids=payload.entity_ids,
        )
    finally:
        conn.close()


@app.post("/selection/tags/apply")
def selection_tags_apply(payload: TagMutationPayload):
    conn = get_db()
    try:
        apply_tags(
            conn,
            entity_type=payload.entity_type,
            entity_ids=payload.entity_ids,
            tag_ids=payload.tag_ids,
        )
        return {"status": "ok"}
    finally:
        conn.close()


@app.post("/selection/tags/remove")
def selection_tags_remove(payload: TagMutationPayload):
    conn = get_db()
    try:
        remove_tags(
            conn,
            entity_type=payload.entity_type,
            entity_ids=payload.entity_ids,
            tag_ids=payload.tag_ids,
        )
        return {"status": "ok"}
    finally:
        conn.close()

# ===================== SIDE PANEL: GENRES =====================

@app.post("/selection/genres")
def selection_genres(payload: SelectionPayload):
    conn = get_db()
    try:
        return genres_for_selection(
            conn,
            entity_type=payload.entity_type,
            entity_ids=payload.entity_ids,
        )
    finally:
        conn.close()


@app.post("/selection/genres/apply")
def selection_genres_apply(payload: GenreMutationPayload):
    conn = get_db()
    try:
        apply_genres(
            conn,
            entity_type=payload.entity_type,
            entity_ids=payload.entity_ids,
            genre_ids=payload.genre_ids,
        )
        return {"status": "ok"}
    finally:
        conn.close()


@app.post("/selection/genres/remove")
def selection_genres_remove(payload: GenreMutationPayload):
    conn = get_db()
    try:
        remove_genres(
            conn,
            entity_type=payload.entity_type,
            entity_ids=payload.entity_ids,
            genre_ids=payload.genre_ids,
        )
        return {"status": "ok"}
    finally:
        conn.close()

# ===================== END =====================

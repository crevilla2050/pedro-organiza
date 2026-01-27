# backend/export_preset_schema.py

from typing import List, Optional
from pydantic import BaseModel, Field


class ExportLayout(BaseModel):
    # Example: "{artist}/{album}/{track:02d} - {title}"
    pattern: str = Field(..., description="Directory/file layout pattern")


class ExportFilters(BaseModel):
    # ---- Genre filters ----
    include_genres: List[str] = Field(default_factory=list)
    exclude_genres: List[str] = Field(default_factory=list)

    # ---- Lifecycle filters ----
    only_states: List[str] = Field(default_factory=list)
    exclude_states: List[str] = Field(default_factory=list)
    exclude_mark_delete: bool = True

    # ---- Artist / Album filters (NEW) ----
    include_artists: List[str] = Field(default_factory=list)
    exclude_artists: List[str] = Field(default_factory=list)

    include_albums: List[str] = Field(default_factory=list)

    min_bitrate: Optional[int] = None
    min_duration: Optional[int] = None
    max_duration: Optional[int] = None


class ExportOptions(BaseModel):
    copy_album_art: bool = True
    allow_delete: bool = False          # destructive exports require explicit opt-in
    incremental: bool = True            # rsync-like behavior


class ExportPreset(BaseModel):
    version: int = 1
    preset_id: str
    name: str
    description: Optional[str] = ""

    target_root: str

    layout: ExportLayout
    filters = ExportFilters(
        include_genres=[g.lower() for g in args.add_genre],
        exclude_genres=[g.lower() for g in args.exclude_genre],

        only_states=args.only_state,
        exclude_states=args.exclude_state,

        exclude_mark_delete=(args.exclude_mark_delete == "yes"),

        include_artists=[a.strip() for a in args.include_artist],
        exclude_artists=[a.strip() for a in args.exclude_artist],

        include_albums=[a.strip() for a in args.include_album],
    )
    options: ExportOptions = ExportOptions()

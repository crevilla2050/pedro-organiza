import re
from pathlib import Path


def safe_component(value: str) -> str:
    if not value:
        return "Unknown"

    value = value.strip()
    value = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", value)
    return value[:120]


def resolve_layout_path(meta: dict, pattern: str) -> Path:
    """
    Resolve layout pattern like:
    "{artist}/{album}/{track} - {title}"
    """

    artist = safe_component(meta.get("artist"))
    album = safe_component(meta.get("album"))
    title = safe_component(meta.get("title"))
    track = meta.get("track") or "00"

    formatted = pattern.format(
        artist=artist,
        album=album,
        title=title,
        track=str(track).zfill(2),
    )

    return Path(formatted)
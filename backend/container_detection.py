import os

def detect_container_from_header(path: str) -> str:
    try:
        with open(path, "rb") as f:
            header = f.read(32)
    except Exception:
        return ""

    if header.startswith(b"fLaC"):
        return "flac"
    if header.startswith(b"RIFF") and b"WAVE" in header:
        return "wav"
    if header.startswith(b"OggS"):
        return "ogg"
    if header.startswith(b"ID3") or header[:2] == b"\xff\xfb":
        return "mp3"
    if b"ftyp" in header:
        return "m4a"
    if header.startswith(b"FORM") and b"AIFF" in header:
        return "aiff"

    return ""
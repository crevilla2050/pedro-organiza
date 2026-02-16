#!/usr/bin/env python3
"""tools/embed_album_art.py

Command-line helper to explicitly embed a provided image into one or more
audio files recorded in the application's database.

This module is designed to be conservative and explicit: it never guesses
which image to use or which files to modify. A user supplies a database
path, an image path and a comma-separated list of file IDs. The script will
optionally embed the (normalized) image into supported audio files and/or
copy a `cover.jpg` next to each file.

High-level behaviour:
- Validates inputs (DB and image exist, file IDs parse)
- Normalizes the image once (shared for all target files)
- Embeds the normalized JPEG into supported formats (.mp3, .flac, .m4a/.mp4)
- Optionally writes a `cover.jpg` file into each audio file's folder

Usage example:
    python tools/embed_album_art.py --db /path/to/db.sqlite --image art.jpg \
        --file-ids 12,23,42 --embed

I18N: user-facing messages are retrieved through `backend.i18n.messages.msg`.
"""

import argparse
import sqlite3
import sys
from pathlib import Path
from datetime import datetime, timezone

from mutagen.id3 import ID3, APIC
from mutagen.flac import FLAC, Picture
from mutagen.mp4 import MP4, MP4Cover

from backend.i18n.messages import msg
from backend.resize_images import normalize_image


# -------------------- CONSTANTS --------------------

SUPPORTED_AUDIO_EXTS = {".mp3", ".flac", ".m4a", ".mp4"}


# -------------------- HELPERS --------------------

def utcnow() -> str:
    """Return current UTC time as an ISO-8601 string.

    This helper is kept small and deterministic for audit logs or debugging.
    """
    return datetime.now(timezone.utc).isoformat()


def read_image_bytes(path: Path) -> bytes:
    """Read raw bytes from `path` and return them.

    A thin wrapper exists so callers read a single shared byte sequence
    (the normalized image) and we can add instrumentation or caching later
    if desired.
    """
    return path.read_bytes()


def embed_mp3(audio_path: Path, image_bytes: bytes):
    """Embed JPEG bytes into an MP3's ID3v2 APIC frame.

    The function removes existing APIC frames before adding the new one to
    avoid duplicated artwork. It saves using ID3v2.3 for broad compatibility.
    """
    audio = ID3(audio_path)
    audio.delall("APIC")
    audio.add(APIC(
        encoding=3,
        mime="image/jpeg",
        type=3,
        desc="Cover",
        data=image_bytes
    ))
    audio.save(v2_version=3)


def embed_flac(audio_path: Path, image_bytes: bytes):
    """Embed JPEG bytes into a FLAC file as a Vorbis picture block.

    We clear existing pictures and add a single picture of type 3 (cover).
    """
    audio = FLAC(audio_path)
    pic = Picture()
    pic.type = 3
    pic.mime = "image/jpeg"
    pic.data = image_bytes
    audio.clear_pictures()
    audio.add_picture(pic)
    audio.save()


def embed_m4a(audio_path: Path, image_bytes: bytes):
    """Embed JPEG bytes into an MP4/M4A file using the `covr` atom.

    `MP4Cover.FORMAT_JPEG` is used so most players will recognize the image.
    """
    audio = MP4(audio_path)
    audio["covr"] = [
        MP4Cover(image_bytes, imageformat=MP4Cover.FORMAT_JPEG)
    ]
    audio.save()


def embed_into_file(audio_path: Path, image_bytes: bytes):
    ext = audio_path.suffix.lower()

    if ext == ".mp3":
        embed_mp3(audio_path, image_bytes)
    elif ext == ".flac":
        embed_flac(audio_path, image_bytes)
    elif ext in {".m4a", ".mp4"}:
        embed_m4a(audio_path, image_bytes)
    else:
        # Unsupported extension — surface a clear, localised error message.
        raise RuntimeError(msg("ERROR_UNSUPPORTED_AUDIO"))


# -------------------- MAIN --------------------

def main():
    parser = argparse.ArgumentParser(
        description=msg("EMBED_ART_DESCRIPTION")
    )

    parser.add_argument(
        "--db",
        required=True,
        help=msg("ARG_DATABASE_PATH")
    )

    parser.add_argument(
        "--image",
        required=True,
        help=msg("ARG_IMAGE_PATH")
    )

    parser.add_argument(
        "--file-ids",
        required=True,
        help=msg("ARG_FILE_IDS")
    )

    parser.add_argument(
        "--embed",
        action="store_true",
        help=msg("ARG_EMBED_ART")
    )

    parser.add_argument(
        "--copy-to-folder",
        action="store_true",
        help=msg("ARG_COPY_TO_FOLDER")
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help=msg("ARG_DRY_RUN")
    )

    args = parser.parse_args()

    # Require at least one action: embed the image or copy it next to files.
    if not args.embed and not args.copy_to_folder:
        print(msg("ERROR_NOTHING_TO_DO"))
        sys.exit(1)

    db_path = Path(args.db)
    image_path = Path(args.image)

    # The supplied image must exist; we will normalize it before use.
    if not image_path.exists():
        print(msg("ERROR_IMAGE_NOT_FOUND"))
        sys.exit(1)

    # Parse comma-separated numeric IDs provided on the CLI. Non-numeric
    # tokens are ignored so callers can safely pass user-typed values.
    file_ids = [
        int(fid.strip())
        for fid in args.file_ids.split(",")
        if fid.strip().isdigit()
    ]

    if not file_ids:
        print(msg("ERROR_NO_FILE_IDS"))
        sys.exit(1)

    # Query the DB for `original_path` for each requested file id. We use
    # parameter substitution to avoid SQL injection and to handle variable
    # length lists of ids.
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    rows = c.execute(
        f"""
        SELECT id, original_path
        FROM files
        WHERE id IN ({",".join("?" for _ in file_ids)})
        """,
        file_ids
    ).fetchall()

    if not rows:
        print(msg("ERROR_FILES_NOT_FOUND"))
        sys.exit(1)

    # Normalize the provided image once. `normalize_image` guarantees a
    # JPEG result suitable for embedding and resizing; it returns truthy on
    # success. We reuse the same normalized bytes for all target files.
    normalized_image_path = image_path.with_suffix(".normalized.jpg")

    processed = normalize_image(
        src_path=image_path,
        dst_path=normalized_image_path
    )

    if not processed:
        print(msg("ERROR_IMAGE_INVALID"))
        sys.exit(1)

    image_bytes = read_image_bytes(normalized_image_path)

    for row in rows:
        audio_path = Path(row["original_path"])

        # Skip unsupported file extensions silently; this mirrors the
        # principle of doing only explicit, non-invasive changes.
        if audio_path.suffix.lower() not in SUPPORTED_AUDIO_EXTS:
            continue

        # Embed the artwork if requested. For safety, support a `--dry-run`
        # mode that prints what would happen instead of modifying files.
        if args.embed:
            if args.dry_run:
                print(
                    msg("DRYRUN_EMBED").format(
                        file=str(audio_path)
                    )
                )
            else:
                embed_into_file(audio_path, image_bytes)
                print(
                    msg("EMBED_SUCCESS").format(
                        file=str(audio_path)
                    )
                )

        # Optionally copy a cover.jpg into the same directory as the audio
        # file. This is useful for some players that look for an image file
        # on disk instead of reading embedded artwork.
        if args.copy_to_folder:
            dst = audio_path.parent / "cover.jpg"
            if args.dry_run:
                print(
                    msg("DRYRUN_COPY").format(
                        file=str(dst)
                    )
                )
            else:
                dst.write_bytes(image_bytes)

    conn.close()

    # Final success message (localized).
    print(msg("EMBED_COMPLETE"))


if __name__ == "__main__":
    main()
# ---------------- END OF FILE ----------------
import os
import re
from pathlib import Path
from typing import Optional

from .config import DEFAULT_DOWNLOAD_FOLDER, CHUNK_SIZE


def sanitize_filename(name: str) -> str:
    invalid_chars_dict = {
        "nt": r'[\\/:*?"<>|]',
        "posix": r"[/:]",
    }
    invalid_chars = invalid_chars_dict.get(os.name, r'[\\/:*?"<>|]')
    return re.sub(invalid_chars, "_", name)


def ensure_download_dir(
    album_name: str,
    base_dir: Optional[str] = None,
) -> str:
    base = base_dir or DEFAULT_DOWNLOAD_FOLDER
    safe_name = sanitize_filename(album_name)
    download_path = Path(base) / safe_name
    download_path.mkdir(parents=True, exist_ok=True)
    return str(download_path)


async def save_image(data: bytes, filepath: str) -> None:
    path = Path(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "wb") as f:
        f.write(data)


def get_filename_from_url(url: str) -> str:
    return url.split("/")[-1]

import re
import shutil
from pathlib import Path

from fastapi import UploadFile


def safe_filename(name: str) -> str:
    base = Path(name).name
    sanitized = re.sub(r"[^A-Za-z0-9._-]", "_", base)
    return sanitized or "upload.xlsx"


def save_upload_file(upload: UploadFile, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("wb") as buffer:
        shutil.copyfileobj(upload.file, buffer)

import os
import uuid
from pathlib import Path

UPLOAD_DIR = Path(__file__).resolve().parents[3] / "data" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

def save_upload_file(upload_file) -> str:
    """Save an uploaded FastAPI UploadFile to disk safely.
    Returns the absolute path to the saved file.
    """
    suffix = Path(upload_file.filename).suffix.lower()
    # generate unique filename to avoid collisions
    unique_name = f"{uuid.uuid4().hex}{suffix}"
    dest_path = UPLOAD_DIR / unique_name
    with dest_path.open("wb") as out_file:
        # FastAPI's UploadFile is async, but here we are in a sync context; reading .file directly works
        out_file.write(upload_file.file.read())
    return str(dest_path)

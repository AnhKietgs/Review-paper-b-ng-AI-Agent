"""Private storage for original uploads and converted Markdown."""

from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile

from app.core.config import Settings


class LocalFileStore:
    """Store immutable content versions under the Docker data volume."""

    def __init__(self, root: Path | None = None):
        self.root = root or Settings.from_env().data_dir

    def save_upload(self, upload: UploadFile, paper_id: str, version: int) -> Path:
        """Stream one upload into a generated path without trusting filename."""
        extension = Path(upload.filename or "").suffix.lower()
        directory = self.root / "uploads" / paper_id
        directory.mkdir(parents=True, exist_ok=True)
        destination = directory / f"v{version}-{uuid4().hex}{extension}"
        with destination.open("wb") as target:
            while block := upload.file.read(1024 * 1024):
                target.write(block)
        upload.file.seek(0)
        return destination

    def save_markdown(self, text: str, paper_id: str, version: int) -> Path:
        """Persist the full MarkItDown result."""
        directory = self.root / "markdown" / paper_id
        directory.mkdir(parents=True, exist_ok=True)
        destination = directory / f"v{version}.md"
        destination.write_text(text, encoding="utf-8")
        return destination

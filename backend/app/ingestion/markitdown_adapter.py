"""MarkItDown converter isolated from domain services."""

from pathlib import Path

from markitdown import MarkItDown


class MarkItDownAdapter:
    """Normalize PDF and DOCX into Markdown."""

    def convert(self, path: Path) -> str:
        """Convert a local upload with MarkItDown."""
        result = MarkItDown().convert(str(path))
        return (result.text_content or "").strip()


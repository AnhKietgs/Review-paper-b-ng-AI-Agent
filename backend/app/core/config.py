"""Environment backed application settings."""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Literal


@dataclass(frozen=True)
class Settings:
    """Configuration shared by API and worker."""

    data_dir: Path
    demo_llm_mode: Literal["fixture", "groq"]
    groq_api_key: str | None
    groq_model: str

    @classmethod
    def from_env(cls) -> "Settings":
        """Load a fresh snapshot without exporting secrets to routes."""
        mode = os.getenv("DEMO_LLM_MODE", "fixture")
        if mode not in {"fixture", "groq"}:
            raise ValueError("DEMO_LLM_MODE must be fixture or groq")
        return cls(
            data_dir=Path(os.getenv("DATA_DIR", "data")),
            demo_llm_mode=mode,
            groq_api_key=os.getenv("GROQ_API_KEY") or None,
            groq_model=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
        )

"""Public health and safe runtime metadata."""

from fastapi import APIRouter

from app.core.config import Settings

router = APIRouter(prefix="/api/v1")


@router.get("/health")
def health() -> dict[str, str]:
    """Return liveness for Compose and users."""
    return {"status": "ok"}


@router.get("/runtime")
def runtime() -> dict[str, str]:
    """Expose demo mode, never environment secrets."""
    return {"llm_mode": Settings.from_env().demo_llm_mode}

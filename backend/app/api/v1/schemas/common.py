"""Common response models."""

from pydantic import BaseModel


class ErrorResponse(BaseModel):
    """Stable error contract."""

    code: str
    detail: str


"""Stable domain errors exposed through the REST boundary."""


class DomainError(Exception):
    """Business failure with a stable machine code."""

    status_code = 500

    def __init__(self, code: str, detail: str):
        super().__init__(detail)
        self.code = code
        self.detail = detail


class NotFoundError(DomainError):
    """Requested resource does not exist in the active library."""

    status_code = 404


class ConflictError(DomainError):
    """Operation conflicts with a resource state."""

    status_code = 409


class ValidationError(DomainError):
    """Input violates a domain rule."""

    status_code = 422


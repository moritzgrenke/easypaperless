"""Custom exception hierarchy for easypaperless."""

from __future__ import annotations


class PaperlessError(Exception):
    """Base exception for all easypaperless errors."""

    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


class AuthError(PaperlessError):
    """Raised on 401 or 403 responses."""


class NotFoundError(PaperlessError):
    """Raised on 404 responses."""


class ValidationError(PaperlessError):
    """Raised on 422 responses or bad input."""


class ServerError(PaperlessError):
    """Raised on 5xx responses or transport errors."""


class UploadError(PaperlessError):
    """Raised when file submission or processing fails."""


class TaskTimeoutError(PaperlessError):
    """Raised when upload polling exceeds the configured timeout."""

    def __init__(self, message: str) -> None:
        super().__init__(message, status_code=None)

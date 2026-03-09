"""
Application exceptions. All are mapped to HTTP responses; never let uncaught
exceptions reach the client. API cannot crash.
"""
from typing import Optional


class AppException(Exception):
    """Base for all app exceptions. Safe to expose message to client."""

    def __init__(self, message: str, details: Optional[dict] = None):
        self.message = message
        self.details = details or {}
        super().__init__(message)


class CatalogLoadError(AppException):
    """Catalog could not be loaded from storage."""
    pass


class ToolNotFoundError(AppException):
    """Tool id not in catalog."""
    pass


class ToolExecutionError(AppException):
    """Tool run failed (MCP or runtime)."""
    pass


class ToolTimeoutError(AppException):
    """Tool run exceeded timeout."""
    pass


class ValidationError(AppException):
    """Invalid request (missing/invalid params)."""
    pass

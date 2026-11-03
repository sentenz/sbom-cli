"""Custom exception types for the Dependency-Track client."""


class Error(Exception):
    """Base exception for Dependency-Track client errors."""


class HTTPError(Error):
    """Raised when the server returns a non-2xx status code."""

    def __init__(self, status_code: int, message: str, url: str) -> None:
        super().__init__(f"HTTP {status_code} error for URL {url}: {message}")
        self.status_code = status_code
        self.url = url


class NotFoundError(Error):
    """Raised when a requested resource is not found (HTTP 404)."""


class ValidationError(Error):
    """Raised when input validation fails."""

"""Define the errors reported by the Dependency-Track client."""


class Error(Exception):
    """Represent a failure reported by the Dependency-Track client."""


class HTTPError(Error):
    """Report an unsuccessful HTTP response other than 404.

    Attributes:
        status_code: HTTP status returned by the server.
        url: Request URL that produced the response.
    """

    def __init__(self, status_code: int, message: str, url: str) -> None:
        """Capture the response status and include the server message in the error.

        Args:
            status_code: HTTP status returned by the server.
            message: Response text or reason phrase.
            url: Request URL that produced the response.
        """
        super().__init__(f"HTTP {status_code} error for URL {url}: {message}")
        self.status_code = status_code
        self.url = url


class NotFoundError(Error):
    """Report an HTTP 404 response from Dependency-Track."""


class ValidationError(Error):
    """Report invalid input or an invalid project lookup response."""

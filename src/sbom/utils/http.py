"""Build HTTP sessions that retry transient Dependency-Track failures."""

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from sbom.resources import constants


def session_retries(
    total_retries: int = constants.HTTP_MAX_RETRIES,
    backoff_factor: float = constants.HTTP_BACKOFF_FACTOR,
    status_forcelist: list[int] | None = None,
) -> requests.Session:
    """Create a requests.Session configured to retry transient HTTP errors.

    Args:
        total_retries: Total number of retry attempts before giving up.
        backoff_factor: Factor for exponential backoff between retries.
        status_forcelist: HTTP status codes that should trigger a retry.
            An empty or omitted list uses the default retryable statuses.

    Returns:
        A session with the retry policy mounted for HTTP and HTTPS.
    """
    session = requests.Session()
    status_forcelist = status_forcelist or constants.HTTP_STATUS

    retry_strategy = Retry(
        total=total_retries,
        status_forcelist=status_forcelist,
        allowed_methods=constants.HTTP_METHODS,
        backoff_factor=backoff_factor,
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("https://", adapter)
    session.mount("http://", adapter)

    return session

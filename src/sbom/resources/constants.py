"""Defining Python Constants for Code Maintainability."""

from http import HTTPMethod, HTTPStatus
from typing import Final

# ─── Application ───────────────────────────────────────────────────
APP_NAME: Final[str] = "sbom"
APP_VERSION: Final[str] = "1.0.0"
APP_DESCRIPTION: Final[str] = "Software Bill of Materials (SBOM) Management Tool"

# ─── API ───────────────────────────────────────────────────────────
API_VERSION: Final[str] = "v1"
API_BASE_PATH: Final[str] = f"/api/{API_VERSION}"
API_ENDPOINT_BOM: Final[str] = f"{API_BASE_PATH}/bom"
API_ENDPOINT_PROJECT: Final[str] = f"{API_BASE_PATH}/project"
API_KEY_HEADER: Final[str] = "X-Api-Key"
API_HEADER_CONTENT_TYPE_JSON: Final[str] = "application/json"
API_HEADER_CONTENT_TYPE_XML: Final[str] = "application/xml"
API_HEADER_DEFAULT: Final[dict[str, str]] = {
    "Content-Type": API_HEADER_CONTENT_TYPE_JSON,
    "Accept": API_HEADER_CONTENT_TYPE_JSON,
}

# ─── HTTP ──────────────────────────────────────────────────────────
HTTP_MAX_RETRIES: Final[int] = 3
HTTP_BACKOFF_FACTOR: Final[float] = 0.5
HTTP_STATUS: Final[list[int]] = [
    HTTPStatus.TOO_MANY_REQUESTS.value,
    HTTPStatus.INTERNAL_SERVER_ERROR.value,
    HTTPStatus.BAD_GATEWAY.value,
    HTTPStatus.SERVICE_UNAVAILABLE.value,
    HTTPStatus.GATEWAY_TIMEOUT.value,
]
HTTP_METHODS: Final[list[str]] = [
    HTTPMethod.GET,
    HTTPMethod.POST,
    HTTPMethod.DELETE,
    HTTPMethod.PUT,
    HTTPMethod.PATCH,
]

# ─── File & Env Names ──────────────────────────────────────────────
ENV_FILE: Final[str] = ".env"
CONFIG_FILES: Final[list[str]] = [
    "~/.sbom/config.yml",
    "/etc/sbom/config.yml",
]

# ─── Miscellaneous ─────────────────────────────────────────────────
DEFAULT_PAGE_SIZE: Final[int] = 100
DEFAULT_MAX_RESULTS: Final[int] = 1000
DEFAULT_TIMEOUT_SECONDS: Final[float] = 30.0
DEFAULT_MAX_RETRIES: Final[int] = 3
DEFAULT_BACKOFF_FACTOR: Final[float] = 0.5


# ─── Logging ───────────────────────────────────────────────────────
LOG_TIME_FORMAT: Final[str] = "%Y-%m-%dT%H:%M:%S%z"
LOG_MESSAGE_FORMAT: Final[str] = (
    "%(asctime)s level=%(levelname)s logger=%(name)s %(message)s"
)

"""
Unit tests for :mod:`sbom.resources.constants`.

These are invariant checks: the API paths, header names, and HTTP retry
settings that the rest of the client depends on.
"""

from __future__ import annotations

from http import HTTPMethod, HTTPStatus

from sbom.resources import constants


class TestApiPaths:
    def test_base_path_uses_version(self) -> None:
        assert constants.API_BASE_PATH == f"/api/{constants.API_VERSION}"

    def test_bom_endpoint(self) -> None:
        assert constants.API_ENDPOINT_BOM == f"{constants.API_BASE_PATH}/bom"

    def test_project_endpoint(self) -> None:
        assert constants.API_ENDPOINT_PROJECT == f"{constants.API_BASE_PATH}/project"

    def test_api_key_header(self) -> None:
        assert constants.API_KEY_HEADER == "X-Api-Key"


class TestHttpSettings:
    def test_retry_status_codes_are_transient(self) -> None:
        expected = {
            HTTPStatus.TOO_MANY_REQUESTS.value,
            HTTPStatus.INTERNAL_SERVER_ERROR.value,
            HTTPStatus.BAD_GATEWAY.value,
            HTTPStatus.SERVICE_UNAVAILABLE.value,
            HTTPStatus.GATEWAY_TIMEOUT.value,
        }
        assert set(constants.HTTP_STATUS) == expected

    def test_retry_methods_are_idempotent_safe_set(self) -> None:
        assert set(constants.HTTP_METHODS) == {
            HTTPMethod.GET,
            HTTPMethod.POST,
            HTTPMethod.DELETE,
            HTTPMethod.PUT,
            HTTPMethod.PATCH,
        }

    def test_timeout_is_positive(self) -> None:
        assert constants.DEFAULT_TIMEOUT_SECONDS > 0

    def test_max_retries_positive(self) -> None:
        assert constants.HTTP_MAX_RETRIES > 0
        assert constants.DEFAULT_MAX_RETRIES > 0

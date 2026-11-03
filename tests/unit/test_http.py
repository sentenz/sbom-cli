"""
Unit tests for :mod:`sbom.utils.http`.

Verifies the retry-enabled session: default and custom retry configuration,
and that adapters are mounted for both http and https.
"""

from __future__ import annotations

import pytest

from sbom.resources import constants
from sbom.utils import http


class TestSessionRetries:
    def test_returns_requests_session(self) -> None:
        session = http.session_retries()
        assert session is not None
        assert hasattr(session, "request")

    def test_adapters_mounted_for_http_and_https(self) -> None:
        session = http.session_retries()
        assert "http://" in session.adapters
        assert "https://" in session.adapters

    def test_default_retry_values(self) -> None:
        session = http.session_retries()
        adapter = session.get_adapter("https://example.com")
        retry = adapter.max_retries
        assert retry.total == constants.HTTP_MAX_RETRIES
        assert retry.backoff_factor == constants.HTTP_BACKOFF_FACTOR
        assert set(retry.status_forcelist) == set(constants.HTTP_STATUS)
        assert set(retry.allowed_methods) == set(constants.HTTP_METHODS)

    def test_custom_retry_values(self) -> None:
        session = http.session_retries(
            total_retries=7,
            backoff_factor=2.0,
            status_forcelist=[500],
        )
        adapter = session.get_adapter("http://example.com")
        retry = adapter.max_retries
        assert retry.total == 7
        assert retry.backoff_factor == 2.0
        assert list(retry.status_forcelist) == [500]

    def test_default_status_forcelist_is_none_uses_constant(self) -> None:
        # Passing status_forcelist=None must fall back to constants.HTTP_STATUS.
        session = http.session_retries(status_forcelist=None)
        retry = session.get_adapter("https://example.com").max_retries
        assert set(retry.status_forcelist) == set(constants.HTTP_STATUS)

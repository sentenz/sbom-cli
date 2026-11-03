"""Table-driven contract tests for retry-enabled HTTP sessions."""

from __future__ import annotations

import pytest
import requests

from sbom.resources import constants
from sbom.utils import http


@pytest.mark.parametrize(
    "kwargs,want_total,want_backoff,want_status",
    [
        pytest.param(
            {},
            constants.HTTP_MAX_RETRIES,
            constants.HTTP_BACKOFF_FACTOR,
            constants.HTTP_STATUS,
            id="defaults",
        ),
        pytest.param(
            {"status_forcelist": None},
            constants.HTTP_MAX_RETRIES,
            constants.HTTP_BACKOFF_FACTOR,
            constants.HTTP_STATUS,
            id="none-status-uses-default",
        ),
        pytest.param(
            {"status_forcelist": []},
            constants.HTTP_MAX_RETRIES,
            constants.HTTP_BACKOFF_FACTOR,
            constants.HTTP_STATUS,
            id="empty-status-uses-default",
        ),
        pytest.param(
            {"total_retries": 7, "backoff_factor": 2.0, "status_forcelist": [500]},
            7,
            2.0,
            [500],
            id="custom-retry-settings",
        ),
        pytest.param(
            {"total_retries": 0, "backoff_factor": 0.0, "status_forcelist": [429, 503]},
            0,
            0.0,
            [429, 503],
            id="zero-retries",
        ),
    ],
)
def test_session_retries_configures_both_schemes(
    kwargs, want_total, want_backoff, want_status
) -> None:
    # Act
    with http.session_retries(**kwargs) as session:
        # Assert
        assert isinstance(session, requests.Session)
        assert "http://" in session.adapters
        assert "https://" in session.adapters
        http_adapter = session.get_adapter("http://example.com")
        https_adapter = session.get_adapter("https://example.com")
        assert http_adapter is https_adapter

        got = https_adapter.max_retries
        assert got.total == want_total
        assert got.backoff_factor == want_backoff
        assert list(got.status_forcelist) == list(want_status)
        assert set(got.allowed_methods) == set(constants.HTTP_METHODS)
        assert got.raise_on_status is False


def test_session_retries_returns_independent_sessions() -> None:
    with http.session_retries() as first, http.session_retries() as second:
        assert first is not second
        assert first.get_adapter("https://example.com") is not second.get_adapter(
            "https://example.com"
        )

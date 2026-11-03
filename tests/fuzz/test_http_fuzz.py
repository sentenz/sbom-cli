"""
Property-based (fuzz) tests for :mod:`sbom.utils.http` using Hypothesis.

Verifies that ``session_retries`` always produces a valid, fully-mounted
session for a wide range of retry configurations, and that the retry adapter
faithfully reflects the requested parameters.
"""

from __future__ import annotations

from hypothesis import example, given, settings
from hypothesis import strategies as st

from sbom.utils import http


class TestSessionRetriesFuzz:
    @given(
        total=st.integers(min_value=0, max_value=100),
        backoff=st.floats(min_value=0.0, max_value=10.0, allow_nan=False, allow_infinity=False),
    )
    @example(total=0, backoff=0.0)
    @example(total=5, backoff=1.5)
    @settings(max_examples=50, deadline=None)
    def test_reflects_requested_retry_params(self, total, backoff) -> None:
        # Act
        session = http.session_retries(total_retries=total, backoff_factor=backoff)

        # Assert (invariants)
        assert "http://" in session.adapters
        assert "https://" in session.adapters
        retry = session.get_adapter("https://example.com").max_retries
        assert retry.total == total
        assert retry.backoff_factor == backoff

    @given(
        status_list=st.lists(st.integers(min_value=100, max_value=599), min_size=1, max_size=10),
    )
    @example(status_list=[500])
    @example(status_list=[429, 500, 503])
    @settings(max_examples=50, deadline=None)
    def test_custom_status_forcelist(self, status_list) -> None:
        # Act
        session = http.session_retries(status_forcelist=status_list)

        # Assert
        retry = session.get_adapter("http://example.com").max_retries
        assert list(retry.status_forcelist) == status_list

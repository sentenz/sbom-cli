"""Property-based invariants for retry-enabled HTTP sessions."""

from __future__ import annotations

from hypothesis import example, given, settings
from hypothesis import strategies as st

from sbom.resources import constants
from sbom.utils import http


class TestSessionRetriesFuzz:
    @given(
        total=st.integers(min_value=0, max_value=100),
        backoff=st.floats(min_value=0.0, max_value=10.0, allow_nan=False, allow_infinity=False),
    )
    @example(total=0, backoff=0.0)
    @example(total=5, backoff=1.5)
    @example(total=100, backoff=10.0)
    @settings(max_examples=50, deadline=None)
    def test_reflects_requested_retry_params(self, total, backoff) -> None:
        # Each generated input owns a fresh session and adapter.
        with http.session_retries(total_retries=total, backoff_factor=backoff) as session:
            http_adapter = session.get_adapter("http://example.com")
            https_adapter = session.get_adapter("https://example.com")

            assert http_adapter is https_adapter
            got = https_adapter.max_retries
            assert got.total == total
            assert got.backoff_factor == backoff
            assert set(got.allowed_methods) == set(constants.HTTP_METHODS)
            assert list(got.status_forcelist) == constants.HTTP_STATUS
            assert got.raise_on_status is False

    @given(
        status_list=st.lists(st.integers(min_value=100, max_value=599), min_size=1, max_size=10),
    )
    @example(status_list=[500])
    @example(status_list=[429, 500, 503])
    @example(status_list=[500, 500])
    @settings(max_examples=50, deadline=None)
    def test_custom_status_forcelist(self, status_list) -> None:
        # Preserve ordering and duplicates; the target must not mutate its input.
        original = list(status_list)
        with http.session_retries(status_forcelist=status_list) as session:
            got = session.get_adapter("http://example.com").max_retries
            assert list(got.status_forcelist) == original
            assert status_list == original

"""
Unit tests for :mod:`sbom.utils.exceptions`.

Verifies the exception hierarchy and the attributes carried by ``HTTPError``.
"""

from __future__ import annotations

import pytest

from sbom.utils import exceptions


class TestHierarchy:
    """All custom errors derive from the base ``Error`` (and ``Exception``)."""

    @pytest.mark.parametrize(
        "exc_cls",
        [
            exceptions.Error,
            exceptions.HTTPError,
            exceptions.NotFoundError,
            exceptions.ValidationError,
        ],
    )
    def test_is_exception_subclass(self, exc_cls) -> None:
        assert issubclass(exc_cls, exceptions.Error)
        assert issubclass(exc_cls, Exception)

    def test_http_and_not_found_are_errors(self) -> None:
        assert issubclass(exceptions.HTTPError, exceptions.Error)
        assert issubclass(exceptions.NotFoundError, exceptions.Error)
        assert issubclass(exceptions.ValidationError, exceptions.Error)


class TestHttpError:
    def test_attributes_and_message(self) -> None:
        err = exceptions.HTTPError(500, "boom", "https://dt.example.com/api/v1/bom")
        assert err.status_code == 500
        assert err.url == "https://dt.example.com/api/v1/bom"
        assert "500" in str(err)
        assert "boom" in str(err)
        assert "https://dt.example.com/api/v1/bom" in str(err)

    def test_catchable_as_base_error(self) -> None:
        with pytest.raises(exceptions.Error):
            raise exceptions.HTTPError(403, "forbidden", "https://x")

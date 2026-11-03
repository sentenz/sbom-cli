"""
Shared pytest fixtures and fakes for the sbom test suite.

Adapts the "Test Fixtures" pattern from the go-unit-testing skill: a small,
reusable setup/teardown mechanism so individual tests stay focused on the
Arrange / Act / Assert logic rather than repeated scaffolding.

No network access is performed anywhere in this suite. HTTP interactions are
simulated with :class:`FakeResponse` / :class:`FakeSession`, which mimic the
subset of the ``requests`` API that :class:`sbom.client.Client` relies on.
"""

from __future__ import annotations

import json
from typing import Any, Callable, Optional

import pytest

from sbom.client import Client


class FakeResponse:
    """Minimal stand-in for ``requests.Response``.

    Only the attributes read by ``Client._send_request`` are implemented:
    ``status_code``, ``content``, ``text``, ``reason``.
    """

    def __init__(
        self,
        status_code: int = 200,
        json_data: Any = None,
        text: str = "",
        reason: str = "",
    ) -> None:
        self.status_code = status_code
        self.reason = reason
        self.text = text
        # When json_data is provided, expose it via .content/.json(); otherwise
        # fall back to the raw text so the "no content" branch is exercised.
        if json_data is not None:
            self._body: bytes = json.dumps(json_data).encode("utf-8")
        else:
            self._body = text.encode("utf-8") if text else b""

    @property
    def content(self) -> bytes:
        return self._body

    def json(self) -> Any:
        if not self._body:
            raise ValueError("No JSON content")
        return json.loads(self._body.decode("utf-8"))


class FakeSession:
    """Minimal stand-in for ``requests.Session``.

    Records every call and returns a canned :class:`FakeResponse` (or raises),
    letting tests assert on the exact URL, method, headers, params, data and
    files that ``Client`` would send.
    """

    def __init__(
        self,
        response: Optional[FakeResponse] = None,
        side_effect: Optional[Callable[..., Any]] = None,
    ) -> None:
        self.response = response or FakeResponse()
        self.side_effect = side_effect
        self.calls: list[dict[str, Any]] = []

    def request(self, **kwargs: Any) -> FakeResponse:
        self.calls.append(kwargs)
        if self.side_effect is not None:
            return self.side_effect(**kwargs)
        return self.response

    @property
    def last_call(self) -> dict[str, Any]:
        return self.calls[-1]


@pytest.fixture
def make_response() -> Callable[..., FakeResponse]:
    """Factory fixture for building canned HTTP responses."""

    def _make(
        status_code: int = 200,
        json_data: Any = None,
        text: str = "",
        reason: str = "",
    ) -> FakeResponse:
        return FakeResponse(
            status_code=status_code,
            json_data=json_data,
            text=text,
            reason=reason,
        )

    return _make


@pytest.fixture
def make_session() -> Callable[..., FakeSession]:
    """Factory fixture for building a fake requests session."""

    def _make(
        response: Optional[FakeResponse] = None,
        side_effect: Optional[Callable[..., Any]] = None,
    ) -> FakeSession:
        return FakeSession(response=response, side_effect=side_effect)

    return _make


@pytest.fixture
def make_client(make_session) -> Callable[..., Client]:
    """Factory fixture for building a Client wired to a fake session.

    Returns a tuple-friendly callable: ``make_client(session=..., **kw)``.
    The fake session is attached to the returned client so tests can inspect
    ``client.session.calls``.
    """

    def _make(
        api_url: str = "https://dt.example.com",
        api_key: str = "test-key",
        verify_ssl: bool = True,
        timeout: float = 30.0,
        session: Optional[FakeSession] = None,
    ) -> Client:
        return Client(
            api_url=api_url,
            api_key=api_key,
            verify_ssl=verify_ssl,
            timeout=timeout,
            session=session or make_session(),
        )

    return _make


@pytest.fixture
def bom_file(tmp_path) -> str:
    """A temporary CycloneDX-ish SBOM file on disk."""
    path = tmp_path / "sbom.cdx.json"
    path.write_text(
        '{"bomFormat": "CycloneDX", "specVersion": "1.5", "version": 1}',
        encoding="utf-8",
    )
    return str(path)

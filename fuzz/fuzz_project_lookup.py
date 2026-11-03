"""Coverage-guided fuzzing of untrusted Dependency-Track project lookup JSON.

Run via `make test-fuzz-guided`. This module is not collected by pytest.
All responses are synthesized in memory; no HTTP connection is attempted.
"""

import sys

import atheris
import requests

# Instrument project code before its first import, not the HTTP test double.
with atheris.instrument_imports():
    from sbom.client import Client
    from sbom.utils import exceptions


PROJECT_NAME = "target"
PROJECT_VERSION = "1"
MAX_INPUT_BYTES = 2048


class _OfflineSession:
    """A deterministic response source that cannot perform network I/O."""

    def __init__(self, body: bytes) -> None:
        response = requests.Response()
        response.status_code = 200
        response._content = body
        response.headers["Content-Type"] = "application/json"
        self.response = response
        self.calls = 0

    def request(self, **kwargs) -> requests.Response:
        self.calls += 1
        assert kwargs["method"] == "GET"
        assert kwargs["url"] == "https://example.invalid/api/v1/project"
        assert kwargs["params"] == {"name": PROJECT_NAME, "version": PROJECT_VERSION}
        assert kwargs["allow_redirects"] is False
        return self.response


def _expected_lookup(response: requests.Response) -> tuple[bool, dict | None]:
    """Derive the lookup oracle from the decoded HTTP payload.

    The decoder is shared deliberately: the invariant under test is the
    application's shape validation, exact matching, and ambiguity handling.
    Malformed JSON must be rejected through the documented validation error.
    """
    try:
        projects = response.json() if response.content else {}
    except ValueError:
        projects = {}

    if not isinstance(projects, list) or any(
        not isinstance(project, dict) for project in projects
    ):
        return False, None

    matches = [
        project
        for project in projects
        if project.get("name") == PROJECT_NAME
        and project.get("version") == PROJECT_VERSION
    ]
    if len(matches) > 1:
        return False, None

    return True, matches[0] if matches else None


@atheris.instrument_func
def test_one_input(data: bytes) -> None:
    """Only documented validation failures are accepted for a response."""
    if len(data) > MAX_INPUT_BYTES:
        return

    session = _OfflineSession(data)
    client = Client(
        api_url="https://example.invalid",
        api_key="offline-fuzz-key",
        session=session,
    )
    valid, expected = _expected_lookup(session.response)

    try:
        actual = client.find_project(name=PROJECT_NAME, version=PROJECT_VERSION)
    except exceptions.ValidationError:
        assert not valid, "A valid project list was incorrectly rejected"
    else:
        assert valid, "A malformed or ambiguous project list was accepted"
        assert actual == expected, "Project lookup violated exact-match semantics"

    assert session.calls == 1, "Project lookup must issue exactly one request"


if __name__ == "__main__":
    atheris.Setup(sys.argv, test_one_input)
    atheris.Fuzz()

"""Fuzz HTTP response decoding and exact project lookup without network I/O."""

import json
import sys

import atheris

with atheris.instrument_imports():
    import requests

    from sbom.client import Client
    from sbom.utils.exceptions import ValidationError


MAX_INPUT_SIZE = 512
PROJECT_NAME = "sbom"
PROJECT_VERSION = "1"


class _ResponseSession:
    """Return one fresh response without constructing a network session."""

    def __init__(self, data: bytes) -> None:
        self.response = requests.Response()
        self.response.status_code = 200
        self.response.encoding = "utf-8"
        self.response._content = data

    def request(self, **kwargs):
        return self.response


def _expected_result(data: bytes) -> tuple[bool, dict | None]:
    """Model the lookup contract independently of the client's filtering code."""
    try:
        projects = json.loads(data.decode("utf-8", errors="replace"))
    except json.JSONDecodeError:
        return False, None

    if not isinstance(projects, list):
        return False, None

    matches = []
    for project in projects:
        if not isinstance(project, dict):
            return False, None
        if "name" not in project or "version" not in project:
            continue
        if (project["name"], project["version"]) == (PROJECT_NAME, PROJECT_VERSION):
            matches.append(project)
    if len(matches) > 1:
        return False, None
    return True, next(iter(matches), None)


@atheris.instrument_func
def test_one_input(data: bytes) -> None:
    """Require a unique exact match, no match, or a validation rejection."""
    # Also bound direct replay inputs; 512 bytes limits JSON nesting/allocations.
    if len(data) > MAX_INPUT_SIZE:
        return

    accepted, expected = _expected_result(data)
    client = Client(
        api_url="https://dependency-track.invalid",
        api_key="fuzz-placeholder",
        session=_ResponseSession(data),
    )
    try:
        actual = client.find_project(PROJECT_NAME, PROJECT_VERSION)
    except ValidationError:
        assert not accepted, "Valid project lookup response was rejected"
        return

    assert accepted, "Invalid or ambiguous project lookup response was accepted"
    # Compare JSON representations so an unrelated NaN field is not a false failure.
    assert json.dumps(actual, sort_keys=True) == json.dumps(expected, sort_keys=True)


if __name__ == "__main__":
    atheris.Setup(sys.argv, test_one_input)
    atheris.Fuzz()

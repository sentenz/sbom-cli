"""
Property-based (fuzz) tests for :mod:`sbom.client` using Hypothesis.
"""

from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest
from hypothesis import example, given, settings
from hypothesis import strategies as st

from sbom.client import Client
from sbom.utils import exceptions


class _StubResponse:
    def __init__(self, status_code: int, json_data=None, text: str = "", reason: str = "") -> None:
        self.status_code = status_code
        self.reason = reason
        self.text = text
        if json_data is not None:
            self.content = json.dumps(json_data).encode("utf-8")
            self._json_data = json_data
        else:
            self.content = text.encode("utf-8") if text else b""
            self._json_data = None

    def json(self):
        if self._json_data is None:
            raise ValueError("No JSON content")
        return self._json_data


class _RecordingSession:
    def __init__(self, response: _StubResponse) -> None:
        self.response = response
        self.last_call = None

    def request(self, **kwargs):
        self.last_call = kwargs
        return self.response


class TestClientInitFuzz:
    @given(
        api_url=st.text(min_size=1, alphabet=st.characters(whitelist_categories=("L", "N", "P", "S"))),
        api_key=st.text(min_size=1),
    )
    @example(api_url="https://dt.example.com/", api_key="test-key")
    @example(api_url="https://dt.example.com///", api_key="k")
    @settings(max_examples=50, deadline=None)
    def test_base_url_is_rstripped(self, api_url, api_key) -> None:
        # Act
        client = Client(api_url=api_url, api_key=api_key)

        # Assert (invariant): base_url is always the rstripped input
        assert client.base_url == api_url.rstrip("/")
        assert client.headers["X-Api-Key"] == api_key


class TestUploadFormFuzz:
    """Invariants on the JSON payload produced by ``upload_sbom``."""

    @given(
        project_name=st.text(min_size=1),
        project_version=st.text(min_size=1),
        auto_create=st.booleans(),
        is_latest=st.booleans(),
        project_tags=st.one_of(st.none(), st.text()),
        parent_uuid=st.one_of(st.none(), st.uuids().map(str)),
    )
    @example(
        project_name="SBOM",
        project_version="1.0.0",
        auto_create=False,
        is_latest=False,
        project_tags=None,
        parent_uuid=None,
    )
    @example(
        project_name="SBOM",
        project_version="1.0.0",
        auto_create=True,
        is_latest=True,
        project_tags="tag-1,tag-2",
        parent_uuid="0760d777-3907-4937-b667-e79d820a393f",
    )
    @settings(max_examples=100, deadline=None)
    def test_form_data_invariants(
        self,
        project_name,
        project_version,
        auto_create,
        is_latest,
        project_tags,
        parent_uuid,
    ) -> None:
        with TemporaryDirectory() as directory:
            bom_file = Path(directory) / "sbom.cdx.json"
            bom_file.write_text(
                '{"bomFormat": "CycloneDX", "specVersion": "1.5", "version": 1}',
                encoding="utf-8",
            )

            # Arrange
            session = _RecordingSession(_StubResponse(200, {"token": "t"}))
            client = Client(
                api_url="https://dt.example.com",
                api_key="test-key",
                session=session,
            )

            # Act
            client.upload_sbom(
                bom_file=str(bom_file),
                auto_create=auto_create,
                project_name=project_name,
                project_version=project_version,
                project_tags=project_tags,
                parent_uuid=parent_uuid,
                is_latest=is_latest,
            )

            # Assert (invariants)
            # Data is now a JSON string, not a dict
            data = json.loads(session.last_call["data"])
            assert data["autoCreate"] in ("true", "false")
            assert data["isLatest"] in ("true", "false")
            assert data["projectName"] == project_name
            assert data["projectVersion"] == project_version
            # Unset optional fields must be omitted entirely (not stringified to
            # the literal "None"). This is the regression guard for the str(None)
            # bug: a None input must never appear as the value "None".
            if project_tags is None:
                assert "projectTags" not in data
            else:
                assert data["projectTags"] == project_tags
            if parent_uuid is None:
                assert "parentUUID" not in data
            else:
                assert data["parentUUID"] == parent_uuid
            # parentName / parentVersion are not supplied here, so they must be absent.
            assert "parentName" not in data
            assert "parentVersion" not in data
            # The BOM file content is now base64-encoded and included in the JSON payload.
            assert "bom" in data
            assert isinstance(data["bom"], str)  # base64-encoded content


class TestSendRequestFuzz:
    """Status-code -> outcome mapping must hold for any 3-digit status."""

    @given(status=st.integers(min_value=100, max_value=599))
    @example(status=200)
    @example(status=204)
    @example(status=404)
    @example(status=500)
    @settings(max_examples=100, deadline=None)
    def test_status_mapping(self, status) -> None:
        # Arrange
        session = _RecordingSession(_StubResponse(status, text="x"))
        client = Client(
            api_url="https://dt.example.com",
            api_key="test-key",
            session=session,
        )

        # Act / Assert
        if 200 <= status < 300:
            result = client._send_request("GET", "/api/v1/project")
            assert isinstance(result, dict)
        elif status == 404:
            with pytest.raises(exceptions.NotFoundError):
                client._send_request("GET", "/api/v1/project")
        else:
            with pytest.raises(exceptions.HTTPError) as exc:
                client._send_request("GET", "/api/v1/project")
            assert exc.value.status_code == status

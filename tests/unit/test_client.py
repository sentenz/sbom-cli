"""
Unit tests for :mod:`sbom.client`.

Adapts the go-unit-testing skill patterns to pytest:
- Table-Driven Testing  -> ``@pytest.mark.parametrize``
- In-Got-Want / AAA     -> explicit arrange / act / assert blocks
- Error Test Template   -> dedicated error-case tables
- Boundary Value Tests  -> empty / whitespace / edge inputs

All HTTP is simulated via the ``FakeSession`` fixture; no network is used.
"""

from __future__ import annotations

import pytest

from sbom.client import Client
from sbom.resources import constants
from sbom.utils import exceptions

# ─── Client.__init__ ───────────────────────────────────────────────


class TestClientInit:
    """Constructor validation and attribute wiring."""

    def test_valid_init_strips_trailing_slash(self, make_client) -> None:
        # Arrange / Act
        client = make_client(api_url="https://dt.example.com/", api_key="k")

        # Assert
        assert client.base_url == "https://dt.example.com"
        assert client.api_key == "k"
        assert client.verify_ssl is True
        assert client.headers[constants.API_KEY_HEADER] == "k"

    def test_empty_api_url_raises(self) -> None:
        with pytest.raises(exceptions.ValidationError):
            Client(api_url="", api_key="k")

    def test_empty_api_key_raises(self) -> None:
        with pytest.raises(exceptions.ValidationError):
            Client(api_url="https://dt.example.com", api_key="")

    def test_custom_timeout_and_verify_ssl(self, make_client) -> None:
        client = make_client(verify_ssl=False, timeout=5.5)
        assert client.verify_ssl is False
        assert client.timeout == 5.5


# ─── _send_request ─────────────────────────────────────────────────


class TestSendRequest:
    """HTTP dispatch, URL building, and status-code handling."""

    @pytest.mark.parametrize(
        "status_code, json_data, expected",
        [
            (200, {"token": "abc"}, {"token": "abc"}),
            (201, {"ok": True}, {"ok": True}),
            (204, None, {}),  # 2xx with no body
        ],
        ids=["200-json", "201-json", "204-empty"],
    )
    def test_success_returns_parsed_json(
        self, make_client, make_session, make_response, status_code, json_data, expected
    ) -> None:
        # Arrange
        session = make_session(response=make_response(status_code, json_data))
        client = make_client(session=session)

        # Act
        got = client._send_request("GET", "/api/v1/project")

        # Assert
        assert got == expected

    def test_success_with_non_json_body_returns_empty(self, make_client, make_session, make_response) -> None:
        # Arrange: 200 with a non-JSON body
        session = make_session(response=make_response(200, text="not json"))
        client = make_client(session=session)

        # Act
        got = client._send_request("GET", "/api/v1/project")

        # Assert
        assert got == {}

    def test_url_is_base_plus_endpoint(self, make_client, make_session) -> None:
        # Arrange
        session = make_session()
        client = make_client(api_url="https://dt.example.com", session=session)

        # Act
        client._send_request("GET", "/api/v1/bom")

        # Assert
        assert session.last_call["url"] == "https://dt.example.com/api/v1/bom"

    def test_headers_and_params_forwarded(self, make_client, make_session) -> None:
        # Arrange
        session = make_session()
        client = make_client(api_key="secret", session=session)

        # Act
        client._send_request("GET", "/api/v1/project", params={"name": "x"})

        # Assert
        call = session.last_call
        assert call["headers"][constants.API_KEY_HEADER] == "secret"
        assert call["params"] == {"name": "x"}
        assert call["verify"] is True

    def test_verify_ssl_false_forwarded(self, make_client, make_session) -> None:
        session = make_session()
        client = make_client(verify_ssl=False, session=session)
        client._send_request("GET", "/api/v1/project")
        assert session.last_call["verify"] is False

    def test_404_raises_not_found(self, make_client, make_session, make_response) -> None:
        session = make_session(response=make_response(404, text="nope"))
        client = make_client(session=session)
        with pytest.raises(exceptions.NotFoundError):
            client._send_request("GET", "/api/v1/project/missing")

    @pytest.mark.parametrize(
        "status_code",
        [400, 401, 403, 500, 502, 503],
        ids=["400", "401", "403", "500", "502", "503"],
    )
    def test_error_status_raises_http_error(
        self, make_client, make_session, make_response, status_code
    ) -> None:
        session = make_session(response=make_response(status_code, text="boom"))
        client = make_client(session=session)
        with pytest.raises(exceptions.HTTPError) as exc:
            client._send_request("GET", "/api/v1/project")
        assert exc.value.status_code == status_code

    def test_network_error_wrapped(self, make_client, make_session) -> None:
        import requests

        def _raise(**kwargs):
            raise requests.ConnectionError("connection refused")

        session = make_session(side_effect=_raise)
        client = make_client(session=session)
        with pytest.raises(exceptions.Error):
            client._send_request("GET", "/api/v1/project")


# ─── upload_sbom ───────────────────────────────────────────────────


class TestUploadSbom:
    """SBOM upload: validation, form-data construction, and dispatch."""

    def test_missing_file_raises(self, make_client, bom_file) -> None:
        client = make_client()
        with pytest.raises(exceptions.ValidationError):
            client.upload_sbom(bom_file="")

    def test_nonexistent_file_raises(self, make_client) -> None:
        client = make_client()
        with pytest.raises(exceptions.ValidationError):
            client.upload_sbom(bom_file="/no/such/file.cdx.json")

    def test_auto_create_requires_name_and_version(self, make_client, bom_file) -> None:
        client = make_client()
        with pytest.raises(exceptions.ValidationError):
            client.upload_sbom(bom_file=bom_file, auto_create=True, project_name="SBOM")

    def test_upload_sends_expected_form_fields(self, make_client, make_session, make_response, bom_file) -> None:
        # Arrange
        session = make_session(response=make_response(200, {"token": "t", "projectUuid": "u"}))
        client = make_client(session=session)

        # Act
        result = client.upload_sbom(
            bom_file=bom_file,
            auto_create=True,
            project_name="SBOM",
            project_version="4.13.4",
            parent_uuid="0760d777-3907-4937-b667-e79d820a393f",
            is_latest=True,
        )

        # Assert
        assert result == {"token": "t", "projectUuid": "u"}
        call = session.last_call
        assert call["method"] == "PUT"
        assert call["url"] == f"https://dt.example.com{constants.API_ENDPOINT_BOM}"

        # Data should be a JSON string
        import json
        data = json.loads(call["data"])
        assert data["autoCreate"] == "true"
        assert data["projectName"] == "SBOM"
        assert data["projectVersion"] == "4.13.4"
        assert data["parentUUID"] == "0760d777-3907-4937-b667-e79d820a393f"
        assert data["isLatest"] == "true"
        # The BOM file content should be base64-encoded in the "bom" field
        assert "bom" in data
        assert isinstance(data["bom"], str)  # base64-encoded content

    def test_upload_omits_unset_optional_fields(self, make_client, make_session, make_response, bom_file) -> None:
        # Arrange: no tags, no parent name/version -> those keys must be absent
        session = make_session(response=make_response(200, {"token": "t"}))
        client = make_client(session=session)

        # Act
        client.upload_sbom(
            bom_file=bom_file,
            auto_create=True,
            project_name="SBOM",
            project_version="1.0.0",
        )

        # Assert
        import json
        data = json.loads(session.last_call["data"])
        assert "projectTags" not in data
        assert "parentName" not in data
        assert "parentVersion" not in data
        assert "parentUUID" not in data
        assert data["autoCreate"] == "true"
        assert data["isLatest"] == "false"

    def test_upload_includes_tags_when_provided(self, make_client, make_session, make_response, bom_file) -> None:
        session = make_session(response=make_response(200, {"token": "t"}))
        client = make_client(session=session)
        client.upload_sbom(
            bom_file=bom_file,
            auto_create=True,
            project_name="SBOM",
            project_version="1.0.0",
            project_tags="tag1,tag2",
        )
        import json
        data = json.loads(session.last_call["data"])
        assert data["projectTags"] == "tag1,tag2"


# ─── delete_project ────────────────────────────────────────────────


class TestDeleteProject:
    def test_empty_uuid_raises(self, make_client) -> None:
        client = make_client()
        with pytest.raises(exceptions.ValidationError):
            client.delete_project(project_uuid="")

    def test_delete_uses_correct_endpoint(self, make_client, make_session, make_response) -> None:
        session = make_session(response=make_response(204))
        client = make_client(session=session)
        client.delete_project(project_uuid="abc-123")
        call = session.last_call
        assert call["method"] == "DELETE"
        assert call["url"] == f"https://dt.example.com{constants.API_ENDPOINT_PROJECT}/abc-123"


# ─── find_project ───────────────────────────────────────────────────────────────


class TestFindProject:
    def test_empty_name_or_version_raises(self, make_client) -> None:
        client = make_client()
        with pytest.raises(exceptions.ValidationError):
            client.find_project(name="", version="1.0")
        with pytest.raises(exceptions.ValidationError):
            client.find_project(name="SBOM", version="")

    def test_returns_first_match(self, make_client, make_session, make_response) -> None:
        projects = [{"uuid": "u1", "name": "SBOM"}, {"uuid": "u2", "name": "SBOM"}]
        session = make_session(response=make_response(200, projects))
        client = make_client(session=session)
        got = client.find_project(name="SBOM", version="4.13.4")
        assert got == {"uuid": "u1", "name": "SBOM"}
        assert session.last_call["params"] == {"name": "SBOM", "version": "4.13.4"}

    def test_returns_none_when_no_match(self, make_client, make_session, make_response) -> None:
        session = make_session(response=make_response(200, []))
        client = make_client(session=session)
        assert client.find_project(name="SBOM", version="4.13.4") is None

    def test_returns_none_when_not_a_list(self, make_client, make_session, make_response) -> None:
        session = make_session(response=make_response(200, {}))
        client = make_client(session=session)
        assert client.find_project(name="SBOM", version="4.13.4") is None

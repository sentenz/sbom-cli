"""Regression tests for transport, configuration, and delete boundaries."""

from unittest.mock import Mock

import pytest
import requests
from requests.adapters import BaseAdapter

from sbom import cli
from sbom.client import Client
from sbom.resources import constants
from sbom.utils import exceptions


@pytest.mark.parametrize("command", ["upload", "delete"])
@pytest.mark.parametrize(
    "environment,flags,expected",
    [(None, [], True), ("false", [], False), ("true", [], True),
     ("false", ["--verify-ssl"], True),
     ("true", ["--no-verify-ssl"], False)],
)
def test_tls_default_and_explicit_overrides(monkeypatch, command, environment, flags, expected):
    monkeypatch.delenv("SBOM_VERIFY_SSL", raising=False)
    monkeypatch.setattr(constants, "CONFIG_FILES", [])
    if environment is not None:
        monkeypatch.setenv("SBOM_VERIFY_SSL", environment)
    args = [command, "--api-url", "https://dt.example", "--api-key", "test"]
    if command == "upload":
        args += ["--file", "bom.json"]
    assert cli.create_parser().parse_args(args + flags).verify_ssl is expected


@pytest.mark.parametrize("status", [301, 302, 303, 307, 308])
@pytest.mark.parametrize("method", ["GET", "PUT", "DELETE"])
@pytest.mark.parametrize("destination", ["https://other.example/steal", "http://dt.example/steal"])
def test_redirects_never_resend_credentials_or_payload(status, method, destination):
    class RedirectAdapter(BaseAdapter):
        def __init__(self):
            self.sent = []

        def send(self, request, **kwargs):
            self.sent.append(request)
            response = requests.Response()
            response.status_code = status
            response.headers["Location"] = destination
            response._content = b"redirect"
            response.request = request
            response.url = request.url
            return response

        def close(self):
            pass

    adapter = RedirectAdapter()
    with requests.Session() as session:
        session.trust_env = False
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        client = Client("https://dt.example", "secret", session=session)
        with pytest.raises(exceptions.HTTPError):
            client._send_request(method, "/api/v1/bom", data="private SBOM")
    assert len(adapter.sent) == 1
    assert adapter.sent[0].url == "https://dt.example/api/v1/bom"


@pytest.mark.parametrize("explicit", [False, True])
def test_dotenv_requires_explicit_path(monkeypatch, tmp_path, explicit):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(constants, "CONFIG_FILES", [])
    for name in ("SBOM_API_URL", "SBOM_API_KEY"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("SBOM_API_KEY", "inherited-key")
    dotenv = tmp_path / ".env"
    dotenv.write_text("SBOM_API_URL=https://from-dotenv.example\n", encoding="utf-8")
    handler = Mock(return_value=0)
    monkeypatch.setattr(cli, "cmd_upload", handler)
    monkeypatch.setattr(cli.log, "setup", lambda: None)
    monkeypatch.setattr(cli.signal, "signal", lambda *args: None)
    argv = ["sbom"] + (["--env-file", str(dotenv)] if explicit else [])
    monkeypatch.setattr(cli.sys, "argv", argv + ["upload", "--file", "bom.json"])
    with pytest.raises(SystemExit) as result:
        cli.main()
    assert result.value.code == (0 if explicit else 2)
    if explicit:
        assert handler.call_args.args[0].api_url == "https://from-dotenv.example"
    else:
        handler.assert_not_called()
    # dotenv mutates os.environ directly; restore this test's addition.
    monkeypatch.delenv("SBOM_API_URL", raising=False)


def test_working_directory_config_is_not_automatic():
    assert ".sbom.yml" not in constants.CONFIG_FILES


@pytest.mark.parametrize("uuid", ["", "../bom", "valid?force=true", None, 123])
def test_invalid_delete_uuid_never_sends_request(make_client, make_session, uuid):
    session = make_session()
    with pytest.raises(exceptions.ValidationError):
        make_client(session=session).delete_project(uuid)
    assert session.calls == []


@pytest.mark.parametrize("projects", [
    {}, [None],
    [{"name": "app", "version": "1", "uuid": "a"},
     {"name": "app", "version": "1", "uuid": "b"}],
])
def test_invalid_or_ambiguous_lookup_fails(make_client, make_session, make_response, projects):
    session = make_session(response=make_response(200, projects))
    with pytest.raises(exceptions.ValidationError):
        make_client(session=session).find_project("app", "1")
    assert len(session.calls) == 1


def test_conflicting_delete_selectors_never_call_client(monkeypatch):
    client = Mock()
    monkeypatch.setattr(cli, "Client", Mock(return_value=client))
    monkeypatch.setattr(constants, "CONFIG_FILES", [])
    args = cli.create_parser().parse_args([
        "delete", "--api-url", "https://dt.example", "--api-key", "test",
        "--project-uuid", "0760d777-3907-4937-b667-e79d820a393f",
        "--project-name", "app", "--project-version", "1",
    ])
    assert cli.cmd_delete(args) == 1
    client.delete_project.assert_not_called()
    client.find_project.assert_not_called()


@pytest.mark.parametrize("projects", [
    [{"name": "app", "version": "2", "uuid": "0760d777-3907-4937-b667-e79d820a393f"}],
    [{"name": "app", "version": "1", "uuid": "../bom"}],
    [{"name": "app", "version": "1", "uuid": "a"},
     {"name": "app", "version": "1", "uuid": "b"}],
    [None], {},
])
def test_delete_lookup_never_deletes_unsafe_result(
    monkeypatch, make_client, make_session, make_response, projects,
):
    session = make_session(response=make_response(200, projects))
    monkeypatch.setattr(cli, "Client", lambda **kwargs: make_client(session=session))
    args = cli.argparse.Namespace(
        api_url="https://dt.example", api_key="test", verify_ssl=True,
        project_uuid=None, project_name="app", project_version="1",
    )
    assert cli.cmd_delete(args) == 1
    assert [call["method"] for call in session.calls] == ["GET"]

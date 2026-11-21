"""
Unit tests for :mod:`sbom.cli`.

Covers:
- ``create_parser``: subcommands and env-var wiring.
- ``cmd_upload`` / ``cmd_delete``: success and failure dispatch, with the
  ``Client`` stubbed out (no network).

The ``Client`` symbol is monkeypatched at the module level so the handlers run
against a deterministic stub.
"""

from __future__ import annotations

import logging
import sys
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from sbom import cli
from sbom.utils import exceptions

# ─── create_parser ───────────────────────────────────────────────────────────────────


class TestCreateParser:
    def test_version_flag_exits_zero(self, capsys) -> None:
        parser = cli.create_parser()

        with pytest.raises(SystemExit) as exc:
            parser.parse_args(["--version"])

        assert exc.value.code == 0
        out = capsys.readouterr().out
        assert "1.0.0" in out

    def test_has_upload_and_delete_subcommands(self) -> None:
        parser = cli.create_parser()
        # Parsing an unknown subcommand should fail; known ones should not.
        args = parser.parse_args(
            ["upload", "-f", "x.json", "-u", "https://x", "-k", "k", "--parent-uuid", "u"]
        )
        assert args.command == "upload"

        args = parser.parse_args(["delete", "-u", "https://x", "-k", "k", "--project-uuid", "u"])
        assert args.command == "delete"

    def test_upload_parent_uuid_is_optional(self, monkeypatch) -> None:
        # Parent UUID is optional since not all uploads require a parent project.
        # Verify that the parser accepts upload subcommand without --parent-uuid.
        monkeypatch.delenv("SBOM_PARENT_UUID", raising=False)
        parser = cli.create_parser()
        args = parser.parse_args([
            "upload",
            "-f", "x.json",
            "-u", "https://x",
            "-k", "k",
            "--project-name", "test",
            "--project-version", "1.0.0",
            "--auto-create",
        ])
        assert args.command == "upload"
        assert args.parent_uuid is None

    def test_env_var_mapping(self) -> None:
        parser = cli.create_parser()
        # Walk the upload subparser's actions and collect env_var mappings.
        env_map = {}
        for action in parser._actions:
            if hasattr(action, "choices") and action.choices:
                for sub in action.choices.values():
                    for a in sub._actions:
                        if getattr(a, "env_var", None):
                            env_map[a.env_var] = a.dest
        assert env_map.get("SBOM_API_URL") == "api_url"
        assert env_map.get("SBOM_API_KEY") == "api_key"
        assert env_map.get("SBOM_PROJECT_NAME") == "project_name"
        assert env_map.get("SBOM_PARENT_UUID") == "parent_uuid"


# ─── cmd_upload ──────────────────────────────────────────────────────────────────────


def _upload_args(**overrides) -> SimpleNamespace:
    base = dict(
        api_url="https://dt.example.com",
        api_key="k",
        verify_ssl=True,
        file="sbom.cdx.json",
        project_uuid=None,
        project_name="SBOM",
        project_version="4.13.4",
        project_tags=None,
        parent_name=None,
        parent_version=None,
        parent_uuid="u",
        is_latest=False,
        auto_create=True,
    )
    base.update(overrides)
    return SimpleNamespace(**base)


class TestCmdUpload:
    def test_success_returns_zero(self, caplog) -> None:
        args = _upload_args()

        with patch.object(cli, "Client", autospec=True) as client_cls:
            client = client_cls.return_value

            with caplog.at_level(logging.INFO, logger="cmd_upload"):
                code = cli.cmd_upload(args)

        assert code == 0
        client_cls.assert_called_once_with(
            api_url=args.api_url,
            api_key=args.api_key,
            verify_ssl=args.verify_ssl,
        )
        client.upload_sbom.assert_called_once_with(
            bom_file=args.file,
            auto_create=args.auto_create,
            project_name=args.project_name,
            project_version=args.project_version,
            project_tags=args.project_tags,
            parent_name=args.parent_name,
            parent_version=args.parent_version,
            parent_uuid=args.parent_uuid,
            is_latest=args.is_latest,
        )

    def test_http_error_returns_one(self) -> None:
        with patch.object(cli, "Client", autospec=True) as client_cls:
            client_cls.return_value.upload_sbom.side_effect = exceptions.HTTPError(
                500,
                "boom",
                "https://x",
            )

            code = cli.cmd_upload(_upload_args())

        assert code == 1

    @pytest.mark.parametrize(
        "raised",
        [
            exceptions.ValidationError("bad input"),
            exceptions.NotFoundError("missing"),
            exceptions.Error("client error"),
            OSError("file error"),
        ],
        ids=["validation", "notfound", "error", "oserror"],
    )
    def test_error_paths_return_one(self, raised) -> None:
        with patch.object(cli, "Client", autospec=True) as client_cls:
            client_cls.return_value.upload_sbom.side_effect = raised

            assert cli.cmd_upload(_upload_args()) == 1

    def test_ssl_disabled_logs_warning(self, caplog) -> None:
        args = _upload_args(verify_ssl=False)

        with patch.object(cli, "Client", autospec=True):
            with caplog.at_level(logging.WARNING, logger="cmd_upload"):
                cli.cmd_upload(args)

        assert any("SSL certificate verification is disabled" in r.message for r in caplog.records)


# ─── cmd_delete ──────────────────────────────────────────────────────────────────────


def _delete_args(**overrides) -> SimpleNamespace:
    base = dict(
        api_url="https://dt.example.com",
        api_key="k",
        verify_ssl=True,
        project_uuid=None,
        project_name=None,
        project_version=None,
    )
    base.update(overrides)
    return SimpleNamespace(**base)


class TestCmdDelete:
    def test_delete_by_uuid(self) -> None:
        args = _delete_args(project_uuid="abc")

        with patch.object(cli, "Client", autospec=True) as client_cls:
            client = client_cls.return_value
            code = cli.cmd_delete(args)

        assert code == 0
        client_cls.assert_called_once_with(
            api_url=args.api_url,
            api_key=args.api_key,
            verify_ssl=args.verify_ssl,
        )
        client.delete_project.assert_called_once_with(project_uuid="abc")
        client.find_project.assert_not_called()

    def test_delete_by_name_version_found(self) -> None:
        args = _delete_args(project_name="SBOM", project_version="4.13.4")

        with patch.object(cli, "Client", autospec=True) as client_cls:
            client = client_cls.return_value
            client.find_project.return_value = {"uuid": "found-uuid"}

            code = cli.cmd_delete(args)

        assert code == 0
        client.find_project.assert_called_once_with(name="SBOM", version="4.13.4")
        client.delete_project.assert_called_once_with(project_uuid="found-uuid")

    def test_delete_by_name_version_not_found(self) -> None:
        with patch.object(cli, "Client", autospec=True) as client_cls:
            client = client_cls.return_value
            client.find_project.return_value = None

            code = cli.cmd_delete(_delete_args(project_name="SBOM", project_version="4.13.4"))

        assert code == 1
        client.find_project.assert_called_once_with(name="SBOM", version="4.13.4")
        client.delete_project.assert_not_called()

    def test_delete_by_name_version_missing_uuid_returns_one(self) -> None:
        with patch.object(cli, "Client", autospec=True) as client_cls:
            client = client_cls.return_value
            client.find_project.return_value = {"name": "SBOM"}

            code = cli.cmd_delete(_delete_args(project_name="SBOM", project_version="4.13.4"))

        assert code == 1
        client.find_project.assert_called_once_with(name="SBOM", version="4.13.4")
        client.delete_project.assert_not_called()

    def test_delete_missing_arguments_returns_one(self) -> None:
        with patch.object(cli, "Client", autospec=True) as client_cls:
            client = client_cls.return_value
            code = cli.cmd_delete(_delete_args())

        assert code == 1
        client.find_project.assert_not_called()
        client.delete_project.assert_not_called()

    def test_delete_http_error_returns_one(self) -> None:
        with patch.object(cli, "Client", autospec=True) as client_cls:
            client_cls.return_value.delete_project.side_effect = exceptions.HTTPError(
                500,
                "boom",
                "https://x",
            )

            assert cli.cmd_delete(_delete_args(project_uuid="abc")) == 1


class TestMain:
    def test_main_version_flag_exits_zero(self, monkeypatch):
        monkeypatch.setattr(cli.log, "setup", lambda: None)
        monkeypatch.setattr(cli.config, "load_environment", lambda: None)
        monkeypatch.setattr(sys, "argv", ["sbom", "--version"])

        with pytest.raises(SystemExit) as exc:
            cli.main()
        assert exc.value.code == 0

    def test_main_upload_dispatch_calls_cmd_upload_and_exits_zero(self, monkeypatch):
        called = {}

        def fake_upload(args):
            called["args"] = args
            return 0

        monkeypatch.setattr(cli, "cmd_upload", fake_upload)
        monkeypatch.setattr(cli.log, "setup", lambda: None)
        monkeypatch.setattr(cli.config, "load_environment", lambda: None)
        monkeypatch.setattr(sys, "argv", [
            "sbom",
            "upload",
            "-f",
            "sbom.cdx.json",
            "-u",
            "https://dt.example.com",
            "-k",
            "k",
            "--parent-uuid",
            "u",
        ])

        with pytest.raises(SystemExit) as exc:
            cli.main()
        assert exc.value.code == 0
        assert "args" in called
        assert called["args"].file == "sbom.cdx.json"

    def test_main_delete_dispatch_calls_cmd_delete_and_exits_zero(self, monkeypatch):
        called = {}

        def fake_delete(args):
            called["args"] = args
            return 0

        monkeypatch.setattr(cli, "cmd_delete", fake_delete)
        monkeypatch.setattr(cli.log, "setup", lambda: None)
        monkeypatch.setattr(cli.config, "load_environment", lambda: None)
        monkeypatch.setattr(sys, "argv", [
            "sbom",
            "delete",
            "-u",
            "https://dt.example.com",
            "-k",
            "k",
            "--project-uuid",
            "abc",
        ])

        with pytest.raises(SystemExit) as exc:
            cli.main()
        assert exc.value.code == 0
        assert called["args"].project_uuid == "abc"

    def test_main_no_subcommand_exits_one(self, monkeypatch):
        monkeypatch.setattr(cli.log, "setup", lambda: None)
        monkeypatch.setattr(cli.config, "load_environment", lambda: None)
        monkeypatch.setattr(sys, "argv", ["sbom"])

        with pytest.raises(SystemExit) as exc:
            cli.main()
        assert exc.value.code == 1

"""Contract tests for environment loading with isolated, table-driven cases."""

from __future__ import annotations

import os

import pytest

from sbom.utils import config


@pytest.mark.parametrize(
    "file_contents,want",
    [
        pytest.param("SBOM_TEST_KEY=hello\n", "hello", id="plain-value"),
        pytest.param("SBOM_TEST_KEY=\n", "", id="empty-value"),
        pytest.param('SBOM_TEST_KEY="hello world"\n', "hello world", id="quoted-spaces"),
        pytest.param("SBOM_TEST_KEY=grüße\n", "grüße", id="unicode-value"),
    ],
)
def test_load_environment_reads_valid_values(tmp_path, monkeypatch, file_contents, want) -> None:
    # Arrange
    monkeypatch.delenv("SBOM_TEST_KEY", raising=False)
    env_file = tmp_path / ".env"
    env_file.write_text(file_contents, encoding="utf-8")

    # Act
    got = config.load_environment(dotenv_path=env_file)

    # Assert
    assert got is True
    assert os.environ["SBOM_TEST_KEY"] == want


@pytest.mark.parametrize(
    "original,override,want",
    [
        pytest.param("original", False, "original", id="preserve-existing"),
        pytest.param("original", True, "from-file", id="replace-existing"),
        pytest.param(None, False, "from-file", id="set-missing-without-override"),
        pytest.param(None, True, "from-file", id="set-missing-with-override"),
    ],
)
def test_load_environment_override(tmp_path, monkeypatch, original, override, want) -> None:
    # Arrange
    if original is None:
        monkeypatch.delenv("SBOM_TEST_OVERRIDE", raising=False)
    else:
        monkeypatch.setenv("SBOM_TEST_OVERRIDE", original)
    env_file = tmp_path / ".env"
    env_file.write_text("SBOM_TEST_OVERRIDE=from-file\n", encoding="utf-8")

    # Act
    got = config.load_environment(dotenv_path=env_file, override=override)

    # Assert
    assert got is True
    assert os.environ["SBOM_TEST_OVERRIDE"] == want


def test_load_environment_missing_file_returns_false(tmp_path, monkeypatch) -> None:
    # Arrange
    monkeypatch.delenv("SBOM_TEST_KEY", raising=False)
    missing = tmp_path / "does-not-exist.env"

    # Act
    got = config.load_environment(dotenv_path=missing)

    # Assert
    assert got is False
    assert "SBOM_TEST_KEY" not in os.environ

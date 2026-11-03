"""
Unit tests for :mod:`sbom.utils.config`.

``load_environment`` wraps ``python-dotenv``'s ``load_dotenv``. Tests use a
temporary ``.env`` file and clean up any variables they introduce so the suite
stays independent (FIRST: Independent).
"""

from __future__ import annotations

import os

import pytest

from sbom.utils import config


@pytest.fixture
def env_cleanup():
    """Snapshot and restore the two variables the tests touch."""
    touched = ["SBOM_TEST_KEY", "SBOM_TEST_OVERRIDE"]
    saved = {k: os.environ.pop(k, None) for k in touched}
    yield
    for k, v in saved.items():
        if v is None:
            os.environ.pop(k, None)
        else:
            os.environ[k] = v


class TestLoadEnvironment:
    def test_loads_variables_from_file(self, tmp_path, env_cleanup) -> None:
        # Arrange
        env_file = tmp_path / ".env"
        env_file.write_text("SBOM_TEST_KEY=hello\n", encoding="utf-8")

        # Act
        result = config.load_environment(dotenv_path=env_file)

        # Assert
        assert result is True
        assert os.environ.get("SBOM_TEST_KEY") == "hello"

    def test_missing_file_returns_false(self, tmp_path, env_cleanup) -> None:
        # Arrange
        missing = tmp_path / "does-not-exist.env"

        # Act
        result = config.load_environment(dotenv_path=missing)

        # Assert
        assert result is False

    def test_override_false_keeps_existing(self, tmp_path, env_cleanup) -> None:
        # Arrange
        os.environ["SBOM_TEST_OVERRIDE"] = "original"
        env_file = tmp_path / ".env"
        env_file.write_text("SBOM_TEST_OVERRIDE=from-file\n", encoding="utf-8")

        # Act
        config.load_environment(dotenv_path=env_file, override=False)

        # Assert
        assert os.environ["SBOM_TEST_OVERRIDE"] == "original"

    def test_override_true_replaces_existing(self, tmp_path, env_cleanup) -> None:
        # Arrange
        os.environ["SBOM_TEST_OVERRIDE"] = "original"
        env_file = tmp_path / ".env"
        env_file.write_text("SBOM_TEST_OVERRIDE=from-file\n", encoding="utf-8")

        # Act
        config.load_environment(dotenv_path=env_file, override=True)

        # Assert
        assert os.environ["SBOM_TEST_OVERRIDE"] == "from-file"

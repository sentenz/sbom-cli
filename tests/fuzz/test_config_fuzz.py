"""Property-based environment loading contracts with per-example state isolation."""

from __future__ import annotations

import os
from pathlib import Path
from tempfile import TemporaryDirectory

from hypothesis import example, given, settings
from hypothesis import strategies as st

from sbom.utils import config

_KEY = "SBOM_FUZZ_KEY"
_SAFE_VALUES = st.text(
    alphabet=st.characters(whitelist_categories=("L", "N"), whitelist_characters="-_./"),
    min_size=0,
    max_size=64,
)


class TestLoadEnvironmentFuzz:
    @given(value=_SAFE_VALUES)
    @example(value="")
    @example(value="alpha-_.42")
    @example(value="grüße")
    @settings(max_examples=50, deadline=None)
    def test_well_formed_line_is_loaded(self, value, monkeypatch) -> None:
        # A function-scoped fixture is not reset between Hypothesis examples.
        # Explicitly capture and restore the variable for *each* generated case.
        with monkeypatch.context() as environment, TemporaryDirectory() as directory:
            environment.setenv(_KEY, "temporary")
            environment.delenv(_KEY)
            env_file = Path(directory) / ".env"
            env_file.write_text(f"{_KEY}={value}\n", encoding="utf-8")

            got = config.load_environment(dotenv_path=env_file, override=True)

            assert got is True
            assert os.environ[_KEY] == value

    @given(value=_SAFE_VALUES)
    @example(value="")
    @example(value="new-value")
    @settings(max_examples=50, deadline=None)
    def test_override_false_preserves_existing_value(self, value, monkeypatch) -> None:
        with monkeypatch.context() as environment, TemporaryDirectory() as directory:
            environment.setenv(_KEY, "preexisting")
            env_file = Path(directory) / ".env"
            env_file.write_text(f"{_KEY}={value}\n", encoding="utf-8")

            got = config.load_environment(dotenv_path=env_file, override=False)

            assert got is True
            assert os.environ[_KEY] == "preexisting"

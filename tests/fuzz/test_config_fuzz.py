"""Property-based environment loading contracts with per-example state isolation."""

from __future__ import annotations

import os
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

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
    def test_well_formed_line_is_loaded(self, value) -> None:
        # Restore all environment changes per example, even when an assertion fails.
        # Avoid function-scoped pytest fixtures under Hypothesis.
        with patch.dict(os.environ), TemporaryDirectory() as directory:
            os.environ.pop(_KEY, None)
            env_file = Path(directory) / ".env"
            env_file.write_text(f"{_KEY}={value}\n", encoding="utf-8")

            got = config.load_environment(dotenv_path=env_file, override=True)

            assert got is True
            assert os.environ[_KEY] == value

    @given(value=_SAFE_VALUES)
    @example(value="")
    @example(value="new-value")
    @settings(max_examples=50, deadline=None)
    def test_override_false_preserves_existing_value(self, value) -> None:
        with patch.dict(os.environ), TemporaryDirectory() as directory:
            os.environ[_KEY] = "preexisting"
            env_file = Path(directory) / ".env"
            env_file.write_text(f"{_KEY}={value}\n", encoding="utf-8")

            got = config.load_environment(dotenv_path=env_file, override=False)

            assert got is True
            assert os.environ[_KEY] == "preexisting"

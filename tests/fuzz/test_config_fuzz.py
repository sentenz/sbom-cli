"""
Property-based (fuzz) tests for :mod:`sbom.utils.config` using Hypothesis.

Property: for any well-formed ``KEY=VALUE`` line written to a ``.env`` file,
``load_environment`` (with ``override=True``) sets that variable in the
environment to exactly ``VALUE``.

Keys are restricted to valid identifiers and values to a safe alphabet so the
test isolates the load behavior from dotenv's quoting/escaping rules.
"""

from __future__ import annotations

import os
from pathlib import Path
from tempfile import TemporaryDirectory

from hypothesis import example, given, settings
from hypothesis import strategies as st

from sbom.utils import config

# A single, fixed key so the test stays independent and easy to clean up.
_KEY = "SBOM_FUZZ_KEY"


class TestLoadEnvironmentFuzz:
    @given(
        value=st.text(
            alphabet=st.characters(whitelist_categories=("L", "N"), whitelist_characters="-_./"),
            min_size=0,
            max_size=64,
        ),
    )
    @example(value="")
    @example(value="alpha-_.42")
    @settings(max_examples=50, deadline=None)
    def test_well_formed_line_is_loaded(self, value) -> None:
        with TemporaryDirectory() as directory:
            # Arrange
            os.environ.pop(_KEY, None)
            env_file = Path(directory) / ".env"
            env_file.write_text(f"{_KEY}={value}\n", encoding="utf-8")

            # Act
            result = config.load_environment(dotenv_path=env_file, override=True)

            # Assert (invariant)
            assert result is True
            assert os.environ.get(_KEY) == value

        # Teardown (keep the suite independent)
        os.environ.pop(_KEY, None)

"""
Unit tests for :mod:`sbom.utils.log`.

``setup`` reconfigures the root logger. Tests assert on the resulting level and
handler, then restore the root logger so they don't leak state (FIRST:
Independent / Repeatable).
"""

from __future__ import annotations

import logging

import pytest

from sbom.utils import log


@pytest.fixture
def restore_root_logger():
    root = logging.getLogger()
    saved_level = root.level
    saved_handlers = list(root.handlers)
    yield
    root.handlers = saved_handlers
    root.setLevel(saved_level)


class TestSetup:
    def test_default_info_level(self, restore_root_logger) -> None:
        log.setup(verbose=False)
        root = logging.getLogger()
        assert root.level == logging.INFO
        assert len(root.handlers) == 1

    def test_verbose_debug_level(self, restore_root_logger) -> None:
        log.setup(verbose=True)
        root = logging.getLogger()
        assert root.level == logging.DEBUG

    def test_handler_writes_to_stdout(self, restore_root_logger, capsys) -> None:
        log.setup(verbose=False)
        logging.getLogger("test").info("hello-structured")
        captured = capsys.readouterr()
        assert "hello-structured" in captured.out

    def test_replaces_existing_handlers(self, restore_root_logger) -> None:
        root = logging.getLogger()
        root.addHandler(logging.NullHandler())
        log.setup(verbose=False)
        # setup() clears handlers and adds exactly one StreamHandler.
        assert len(root.handlers) == 1
        assert isinstance(root.handlers[0], logging.StreamHandler)

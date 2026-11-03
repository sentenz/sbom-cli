"""Logging configuration for the SBOM CLI."""

import logging
import sys

from sbom.resources import constants


def setup(verbose: bool = False) -> None:
    """Configure root-level logging to stdout in a structured format.

    Uses a structured key=value format in each log record. By default,
    logs at INFO level; if ``verbose`` is True, logs at DEBUG level.

    Args:
        verbose: Whether to enable DEBUG-level logging.
    """
    level = logging.DEBUG if verbose else logging.INFO
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter(constants.LOG_MESSAGE_FORMAT, constants.LOG_TIME_FORMAT)
    )

    root = logging.getLogger()
    root.setLevel(level)
    root.handlers.clear()
    root.addHandler(handler)

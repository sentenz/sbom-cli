"""Configure structured logging for SBOM commands."""

import logging
import sys

from sbom.resources import constants


def setup(verbose: bool = False) -> None:
    """Replace root log handlers with a structured stdout handler.

    Args:
        verbose: Enable debug logging. The default level is INFO.
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

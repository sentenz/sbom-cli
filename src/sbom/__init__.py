"""Manage SBOMs on Dependency-Track through the client and CLI."""

from sbom.resources import constants

__version__ = constants.APP_VERSION
__author__ = "SBOM Contributors"
__license__ = "Apache-2.0"

__all__ = [
    "__version__",
    "constants",
]

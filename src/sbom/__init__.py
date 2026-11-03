"""
SBOM CLI - Software Bill of Materials Management Tool

A command-line interface for managing SBOMs on OWASP Dependency-Track servers.

Modules:
    - client: Dependency-Track API client
    - cli: Command-line interface
    - resources: Constants and configuration
    - utils: Utility functions (HTTP, config, logging, exceptions)
"""

from sbom.resources import constants

__version__ = constants.APP_VERSION
__author__ = "SBOM Contributors"
__license__ = "Apache-2.0"

__all__ = [
    "__version__",
    "constants",
]

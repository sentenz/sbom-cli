"""
Main entry point for the SBOM CLI package.

Enables running the CLI via: python -m sbom
"""

import sys

from sbom.cli import main

if __name__ == "__main__":
    sys.exit(main() or 0)

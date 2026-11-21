"""Run the SBOM command line with `python -m sbom.main`."""

import sys

from sbom.cli import main

if __name__ == "__main__":
    sys.exit(main() or 0)

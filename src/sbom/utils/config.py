"""Environment configuration helpers for the SBOM CLI."""

from pathlib import Path

from dotenv import load_dotenv

from sbom.resources import constants


def load_environment(
    dotenv_path: Path | str = constants.ENV_FILE,
    override: bool = False,
    verbose: bool = False,
) -> bool:
    """
    Load environment variables from a .env file if present.

    Args:
        dotenv_path: Path to .env file (default: looks for '.env' in the
            current directory).
        override: Whether to override existing environment variables
        verbose: Enable verbose output from python-dotenv

    Returns:
        True if loaded successfully, False otherwise
    """
    return load_dotenv(
        dotenv_path=dotenv_path,
        override=override,
        verbose=verbose,
    )

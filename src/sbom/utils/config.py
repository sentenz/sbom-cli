"""Load dotenv settings for the SBOM CLI."""

from pathlib import Path

from dotenv import load_dotenv

from sbom.resources import constants


def load_environment(
    dotenv_path: Path | str = constants.ENV_FILE,
    override: bool = False,
    verbose: bool = False,
) -> bool:
    """Load settings from a dotenv file into the process environment.

    Args:
        dotenv_path: File to read, relative to the working directory or absolute.
        override: Whether file values replace existing environment variables.
        verbose: Whether to report a missing file.

    Returns:
        True if dotenv loading is enabled and the file contains entries.
    """
    return load_dotenv(
        dotenv_path=dotenv_path,
        override=override,
        verbose=verbose,
    )

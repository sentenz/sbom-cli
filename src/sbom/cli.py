"""Parse SBOM commands and report upload and deletion outcomes."""

import argparse
import logging
import signal
import sys
from pathlib import Path
from types import FrameType

import configargparse

from sbom.client import Client
from sbom.resources import constants
from sbom.utils import config, exceptions, log


def cmd_upload(args: argparse.Namespace) -> int:
    """Upload an SBOM and log the result.

    Args:
        args: Connection settings, SBOM path, and project metadata from the
            upload subcommand.

    Returns:
        Zero on success or one if the upload operation fails.

    Raises:
        exceptions.ValidationError: The server URL or API key is empty.
    """
    logger = logging.getLogger("cmd_upload")
    # XXX Warn about SSL verification being disabled
    if not args.verify_ssl:
        logger.warning(
            "event=security SSL certificate verification is "
            "disabled for request to %s",
            args.api_url,
        )

    client = Client(
        api_url=args.api_url,
        api_key=args.api_key,
        verify_ssl=args.verify_ssl,
    )

    try:
        client.upload_sbom(
            bom_file=args.file,
            auto_create=args.auto_create,
            project_name=args.project_name,
            project_version=args.project_version,
            project_tags=args.project_tags,
            parent_name=args.parent_name,
            parent_version=args.parent_version,
            parent_uuid=args.parent_uuid,
            is_latest=args.is_latest,
        )

        logger.info(
            "event=upload_success project_name=%s project_version=%s",
            args.project_name or "",
            args.project_version or "",
        )
        return 0

    except exceptions.ValidationError as e:
        logger.error('event=validation_error error="%s"', e)
        return 1
    except exceptions.NotFoundError as e:
        logger.error('event=resource_not_found error="%s"', e)
        return 1
    except exceptions.HTTPError as e:
        logger.error(
            'event=http_error status=%d url=%s error="%s"',
            e.status_code,
            e.url,
            str(e),
        )
        return 1
    except exceptions.Error as e:
        logger.error('event=client_error error="%s"', e)
        return 1
    except OSError as e:
        logger.error('event=file_error error="%s"', e)
        return 1
    except KeyboardInterrupt:
        logger.error('event=interrupted error="Upload interrupted by user"')
        return 1
    except Exception as e:
        logger.error('event=unexpected_error error="%s"', e)
        return 1


def cmd_delete(args: argparse.Namespace) -> int:
    """Delete a project and log the result.

    Args:
        args: Connection settings and either a project UUID or an exact name
            and version from the delete subcommand.

    Returns:
        Zero on success or one if the delete operation fails.

    Raises:
        exceptions.ValidationError: The server URL or API key is empty.
    """
    logger = logging.getLogger("cmd_delete")
    # XXX Warn about SSL verification being disabled
    if not args.verify_ssl:
        logger.warning(
            "event=security SSL certificate verification is "
            "disabled for request to %s",
            args.api_url,
        )

    client = Client(
        api_url=args.api_url,
        api_key=args.api_key,
        verify_ssl=args.verify_ssl,
    )

    try:
        if args.project_uuid:
            if args.project_name or args.project_version:
                raise exceptions.ValidationError(
                    "Specify either project UUID or name and version, not both."
                )
            client.delete_project(project_uuid=args.project_uuid)
            logger.info("event=delete_success project_uuid=%s", args.project_uuid)
            return 0

        if args.project_name and args.project_version:
            project = client.find_project(
                name=args.project_name, version=args.project_version
            )
            if project is None:
                logger.error(
                    "event=project_not_found name=%s version=%s",
                    args.project_name,
                    args.project_version,
                )
                return 1

            project_uuid = project.get("uuid")
            if not project_uuid:
                logger.error(
                    "event=lookup_error "
                    'reason="Found project missing `uuid` field" '
                    "name=%s version=%s",
                    args.project_name,
                    args.project_version,
                )
                return 1

            client.delete_project(project_uuid=project_uuid)
            logger.info(
                "event=delete_success name=%s version=%s uuid=%s",
                args.project_name,
                args.project_version,
                project_uuid,
            )
            return 0

        logger.error(
            "event=invalid_arguments "
            'reason="Either --project-uuid or both --project-name and '
            "--project-version must be specified."
        )
        return 1

    except exceptions.ValidationError as e:
        logger.error('event=validation_error error="%s"', e)
        return 1
    except exceptions.NotFoundError as e:
        logger.error('event=resource_not_found error="%s"', e)
        return 1
    except exceptions.HTTPError as e:
        logger.error(
            'event=http_error status=%d url=%s error="%s"',
            e.status_code,
            e.url,
            str(e),
        )
        return 1
    except exceptions.Error as e:
        logger.error('event=client_error error="%s"', e)
        return 1
    except KeyboardInterrupt:
        logger.error('event=interrupted error="Delete interrupted by user"')
        return 1
    except Exception as e:
        logger.error('event=unexpected_error error="%s"', e)
        return 1


def create_parser() -> configargparse.ArgParser:
    """Build the parser for SBOM upload and project deletion.

    Returns:
        A parser that resolves command options from flags, environment
        variables, and configuration files in descending priority.
    """
    parser = configargparse.ArgParser(
        prog=constants.APP_NAME,
        description=constants.APP_DESCRIPTION,
        add_config_file_help=True,
    )
    parser.add(
        "--env-file",
        help="Load a trusted dotenv file explicitly (before the subcommand)",
    )
    parser.add(
        "-V",
        "--version",
        action="version",
        version=f"%(prog)s {constants.APP_VERSION}",
        help="Show the SBOM CLI version and exit",
    )

    subparsers = parser.add_subparsers(
        dest="command",
        required=False,
        help="Available SBOM operations",
    )

    # ─── Parent Command ────────────────────────────────────────────
    parent_parser = configargparse.ArgParser(add_help=True)
    parent_parser.add(
        "-u",
        "--api-url",
        env_var="SBOM_API_URL",
        required=True,
        help="API base URL for service",
    )
    parent_parser.add(
        "-k",
        "--api-key",
        env_var="SBOM_API_KEY",
        required=True,
        help="API key for authenticating with the server",
    )
    parent_parser.add(
        "--verify-ssl",
        env_var="SBOM_VERIFY_SSL",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Verify SSL certificates (default: true)",
    )

    # ─── Upload Subcommand ─────────────────────────────────────────
    upload_parser = subparsers.add_parser(
        "upload",
        parents=[parent_parser],
        default_config_files=constants.CONFIG_FILES,
        add_help=False,
        help="Upload an SBOM file to the server",
    )
    upload_parser.add(
        "-f",
        "--file",
        required=True,
        help="Path to the SBOM file to upload",
    )
    upload_parser.add(
        "--project-uuid",
        env_var="SBOM_PROJECT_UUID",
        help="Existing project UUID",
    )
    upload_parser.add(
        "--project-name",
        env_var="SBOM_PROJECT_NAME",
        help="Project name (for auto-create)",
    )
    upload_parser.add(
        "--project-version",
        env_var="SBOM_PROJECT_VERSION",
        help="Project version (for auto-create)",
    )
    upload_parser.add(
        "--project-tags",
        help="Comma-separated project tags",
    )
    upload_parser.add(
        "--parent-name",
        env_var="SBOM_PARENT_NAME",
        help="Parent project name",
    )
    upload_parser.add(
        "--parent-version",
        help="Parent project version",
    )
    upload_parser.add(
        "--parent-uuid",
        env_var="SBOM_PARENT_UUID",
        help="Parent project UUID (optional)",
    )
    upload_parser.add(
        "--is-latest",
        env_var="SBOM_IS_LATEST",
        action="store_true",
        help="Mark this SBOM as the latest version",
    )
    upload_parser.add_argument(
        "--auto-create",
        env_var="SBOM_AUTO_CREATE",
        action="store_true",
        help=(
            "Automatically create the project if it does not already "
            "exist (default: true)"
        ),
    )

    # ─── Delete Subcommand ─────────────────────────────────────────
    delete_parser = subparsers.add_parser(
        "delete",
        parents=[parent_parser],
        default_config_files=constants.CONFIG_FILES,
        add_help=False,
        help="Delete a project (and its SBOM) from the server",
    )
    delete_parser.add(
        "--project-uuid",
        env_var="SBOM_PROJECT_UUID",
        help="Project UUID to delete",
    )
    delete_parser.add(
        "--project-name",
        env_var="SBOM_PROJECT_NAME",
        help="Project name to delete",
    )
    delete_parser.add(
        "--project-version",
        env_var="SBOM_PROJECT_VERSION",
        help="Project version to delete (required when using name)",
    )

    return parser


def main() -> None:
    """Run the selected SBOM command and exit with its status.

    Configure logging, load an explicitly selected dotenv file, and handle
    termination signals while dispatching the command.

    Raises:
        SystemExit: Argument parsing or command execution has finished.
    """
    log.setup()

    # Only an explicit CLI path may authorize loading environment settings.
    bootstrap = argparse.ArgumentParser(add_help=False, allow_abbrev=False)
    bootstrap.add_argument("--env-file")
    selected, _ = bootstrap.parse_known_args()
    if selected.env_file:
        if not Path(selected.env_file).is_file():
            bootstrap.error("--env-file must name an existing file")
        config.load_environment(dotenv_path=selected.env_file)

    parser = create_parser()
    args = parser.parse_args()

    # Gracefully handle SIGINT and SIGTERM
    def _signal_handler(signum: int, frame: FrameType | None) -> None:
        """Log the termination signal and exit with status one.

        Args:
            signum: Signal number received by the process.
            frame: Interrupted stack frame supplied by the signal handler.

        Raises:
            SystemExit: The process received a termination signal.
        """
        logger = logging.getLogger("main")
        logger.error("event=signal_received signal=%d", signum)
        sys.exit(1)

    signal.signal(signal.SIGINT, _signal_handler)
    signal.signal(signal.SIGTERM, _signal_handler)

    if args.command == "upload":
        exit_code = cmd_upload(args)
        sys.exit(exit_code)
    elif args.command == "delete":
        exit_code = cmd_delete(args)
        sys.exit(exit_code)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()

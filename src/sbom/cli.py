"""
Command-line interface for the SBOM tool.
This module provides the main entry point for the SBOM CLI,
including command parsing, subcommand handling, and structured logging.
"""

import argparse
import logging
import signal
import sys
from types import FrameType

import configargparse
import urllib3

from sbom.client import Client
from sbom.resources import constants
from sbom.utils import config, exceptions, log


def cmd_upload(args: argparse.Namespace) -> int:
    """Handle the 'upload' subcommand: upload an SBOM file.

    Builds arguments for Client.upload_sbom, invokes it, and logs success
    or failure with structured messages.

    Args:
        args: Parsed namespace from configargparse, containing api_url,
            api_key, verify_ssl, file, project_uuid, project_name,
            project_version, project_tags, parent_name, parent_version,
            parent_uuid, is_latest, and auto_create.

    Returns:
        Exit code: 0 on success, 1 on any failure.
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
    """Handle the 'delete' subcommand: delete a project (and its SBOM).

    If ``--project-uuid`` is provided, deletes by UUID. Otherwise, if both
    ``--project-name`` and ``--project-version`` are provided, looks up the
    project to obtain its UUID and then deletes it. Logs structured events.

    Args:
        args: Parsed namespace from configargparse, containing api_url,
            api_key, verify_ssl, project_uuid, project_name, and
            project_version.

    Returns:
        Exit code: 0 on success, 1 on any failure.
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
    """Create the command-line parser with subcommands.

    Global options (flags > environment variables > config files) include:
    --api-url (required), --api-key (required), and --verify-ssl.

    Subcommands:
        upload:
            --file (required): Path to the SBOM file.
            --project-uuid: Existing project UUID.
            --project-name: Project name for auto-create.
            --project-version: Project version for auto-create.
            --project-tags: Comma-separated tags.
            --parent-name: Parent project name.
            --parent-version: Parent project version.
            --parent-uuid: Parent project UUID.
            --is-latest: Mark as the latest version.
            --auto-create: Create project if not present.
        delete:
            --project-uuid: Project UUID to delete.
            --project-name: Project name to delete.
            --project-version: Project version to delete.

    Returns:
        An initialized ArgParser.
    """
    parser = configargparse.ArgParser(
        prog=constants.APP_NAME,
        description=constants.APP_DESCRIPTION,
        default_config_files=constants.CONFIG_FILES,
        add_config_file_help=True,
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
        action="store_true",
        help="Verify SSL certificates (default: true)",
    )

    # ─── Upload Subcommand ─────────────────────────────────────────
    upload_parser = subparsers.add_parser(
        "upload",
        parents=[parent_parser],
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
    """Main entry point for the SBOM CLI.

    Parses arguments, configures logging, registers signal handlers, and
    dispatches to the appropriate subcommand handler.
    """

    # XXX Disable InsecureRequestWarning from `urllib3`
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    log.setup()

    config.load_environment()

    parser = create_parser()
    args = parser.parse_args()

    # Gracefully handle SIGINT and SIGTERM
    def _signal_handler(signum: int, frame: FrameType | None) -> None:
        """Handle termination signals by logging and exiting."""
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

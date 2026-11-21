# SBOM CLI

The SBOM tool provides a command-line interface (CLI) for managing Software Bill of Materials (SBOM) files on an API server, such as OWASP Dependency-Track.

- [1. Details](#1-details)
  - [1.1. Prerequisites](#11-prerequisites)
  - [1.2. Insights](#12-insights)
  - [1.3. Configuration](#13-configuration)
    - [1.3.1. Environment Variables](#131-environment-variables)
    - [1.3.2. Constants](#132-constants)
- [2. Usage](#2-usage)
  - [2.1. Installation](#21-installation)
  - [2.2. Upload Methods](#22-upload-methods)
  - [2.3. Access Control](#23-access-control)
- [3. Contribution](#3-contribution)
- [4. Troubleshoot](#4-troubleshoot)
- [5. References](#5-references)

## 1. Details

### 1.1. Prerequisites

- [Python](https://www.python.org/downloads/)
  > Python 3.8 or higher is required.

- [pip](https://pip.pypa.io/en/stable/installation/)
  > pip is required to install Python dependencies for the CLI.

- [Docker](https://www.docker.com/get-started/)
  > Docker is required to run the containerized CLI.

### 1.2. Insights

- [CLI reference](docs/cli.md) · [Documentation site](https://sentenz.github.io/sbom-cli/)
  > Lists flags, environment variables, configuration keys, and defaults for each command.

- [REST API](docs/rest-api.md)
  > Provides detailed information on the available REST API endpoints for managing SBOM files.

- [Order of Precedence](docs/order-of-precedence.md)
  > Explains the hierarchy of configuration sources and the order of precedence in the SBOM CLI.

- [Upload Methods](docs/upload-methods.md)
  > Provides detailed instructions to upload SBOM files using the CLI.

To rebuild the reference and preview the documentation from the repository root, run these commands in a Python 3.12 virtual environment.

```bash
python -m pip install -e '.[docs]'
python scripts/generate_cli_docs.py
zensical serve
```

Run `zensical build --clean --strict` to build the static files in `site/`. Commit `docs/cli.md` alongside changes to the parser. The Documentation workflow checks the generated reference on pull requests and deploys from `main`. For the first deployment, select **GitHub Actions** under **Settings → Pages → Build and deployment → Source**.

### 1.3. Configuration

#### 1.3.1. Environment Variables

> [!IMPORTANT]
> Use HTTPS (`verify_ssl=true`) in production to ensure secure communication with the Dependency-Track API.

The [CLI reference](docs/cli.md) lists the environment bindings for each command. Supply `SBOM_API_KEY` through the shell or a CI secret. See [configuration precedence](docs/order-of-precedence.md) when the same option appears in several sources.

#### 1.3.2. Constants

1. Concepts and Benefits

    - [x] Module-Level Constants
      > [!NOTE]
      > Python does not support true constants names. Using the uppercase identifier convention signals immutability and public intent, and does not prevent reassignment. Avoid reassignment or mutation, even if not enforced at runtime, to preserve semantic clarity.

    - [x] Type-Annotating Constants
      > [!IMPORTANT]
      > Static type checkers (e.g., mypy, pyright, pyre) and linters (e.g., pylint, ruff) detect Final and Literal annotations through introspection of the AST (Abstract Syntax Tree) and typing module semantics.
      >
      > `typing.Final` (PEP 591) annotation registers a variable as immutable, reassignments raise a diagnostic warning.
      >
      > `typing.Literal` (PEP 586) annotation treats a variable as a value constraint, only the specified literals are valid for assignment.

    - [x] Enumerations Constants
      > [!IMPORTANT]
      > Constants defined via `enum.Enum` and the stricter `@unique` decorator are identified by static analyzers and IDEs as symbolic, type-safe constants. Enumeration Constants can be verified at runtime or statically.

2. Examples and Explanation

    - Module-Level Constants

      ```markdown
      .
      └── modules
          └── <package>
              └── resources
                  └── constants.py
      ```

    - Type-Annotating Constants

      ```python
      from typing import Final

      MAX_SPEED: Final[int] = 300
      DEFAULT_COLOR: Final[str] = "\033[1;34m"
      ALLOWED_BUILTINS: Final[tuple[str, ...]] = ("sum", "max", "min", "abs")
      ```

    - Enumerations Constants

      ```python
      from enum import Enum, unique

      @unique
      class LogLevel(Enum):
          """Logging Levels Enum."""

          DEBUG = "DEBUG"
          INFO = "INFO"
          WARNING = "WARNING"
          ERROR = "ERROR"
          CRITICAL = "CRITICAL"
      ```

## 2. Usage

### 2.1. Installation

- Python CLI

  ```bash
  pip install sbom
  ```

- Containerized CLI

  ```bash
  docker build -t sbom:latest .
  ```

### 2.2. Upload Methods

[Upload Methods](docs/upload-methods.md) provides detailed instructions to upload SBOM files using the CLI.

- Python CLI

  Uses the installed `sbom` command and a [trusted dotenv file](docs/upload-methods.md#11-dotenv-file).

  ```bash
  sbom --env-file .env upload -f logs/sbom/sbom-image.cdx.json
  ```

- Containerized CLI

  Uses the containerized version of the `sbom` CLI tool.

  ```bash
  make container-docker-run CONTAINER_IMAGE=sbom CONTAINER_TAG=latest \
    ARGS="upload -f logs/sbom/sbom-image.cdx.json"
  ```

### 2.3. Access Control

Create an API key in the Dependency-Track UI and export it as `SBOM_API_KEY`, or load a trusted dotenv file explicitly with `sbom --env-file /path/to/.env upload ...`. Dotenv files in the working directory are no longer loaded automatically.

- [Permissions](https://dependencytrack.github.io/docs/next/reference/permissions/)
  > Ensure the API key has the necessary permissions for BOM upload and project creation (if using auto-create).

  | Permission                | Description                                               |
  | ------------------------- | --------------------------------------------------------- |
  | `BOM_UPLOAD`              | Upload CycloneDX Software Bills of Materials.             |
  | `PROJECT_CREATION_UPLOAD` | Auto-create a project on BOM upload if it does not exist. |

- [.env](#131-environment-variables)
  > Replace `<api_key>` with the actual API key obtained from the Dependency-Track UI.

  ```env
  SBOM_API_KEY=<api_key>
  ```

## 3. Contribution

[CONTRIBUTING.md](CONTRIBUTING.md) provides guidance and instructions for contributing to the project.

- [AI Agents](CONTRIBUTING.md#1-ai-agents)
  > Automated tools that assist in various development tasks such as code generation, testing, and documentation.

- [Skills Manager](CONTRIBUTING.md#2-skills-manager)
  > CLI tool for managing AI agent skills in development projects.

- [Task Runner](CONTRIBUTING.md#3-task-runner)
  > Make automation tool that defines and manages tasks to streamline development workflows.

- [Secrets Manager](CONTRIBUTING.md#9-secrets-manager)
  > Manage and secure sensitive information such as API keys, passwords, and certificates.

## 4. Troubleshoot

- [File Permission Issues](docs/troubleshoot.md#11-file-permission-issues)
  > Ensure that the SBOM file has the correct permissions and is readable by the user or process running the SBOM CLI.

- [Authentication Errors](docs/troubleshoot.md#12-authentication-errors)
  > Ensure that the API key is correctly set in the environment variables and has the necessary permissions.

- [Connection Refused](docs/troubleshoot.md#13-connection-refused)
  > Ensure that the Dependency-Track server is running and the hostname is correctly resolvable.

- [DNS Resolution Errors](docs/troubleshoot.md#14-dns-resolution-errors)
  > Ensure that the hostname of the Dependency-Track server is resolvable from the network.

## 5. References

- OWASP [CycloneDX](https://cyclonedx.org/) specification.

# Configuration Precedence

The [Command Line Interface (CLI)](https://clig.dev/) supports multiple configuration sources with a specific order of precedence.

- [1. CLI](#1-cli)
  - [1.1. Order of Precedence](#11-order-of-precedence)
  - [1.2. Supported Configuration Sources](#12-supported-configuration-sources)
  - [1.3. Examples and Explanation](#13-examples-and-explanation)
  - [1.4. Table of Comparison](#14-table-of-comparison)
- [2. References](#2-references)

## 1. CLI

### 1.1. Order of Precedence

> [!NOTE]
> The SBOM CLI supports multiple configuration sources in order of priority (highest → lowest).

1. Command-Line Flags
2. Environment Variables (Env Vars)
3. Dotenv Files (`.env`)
4. Config Files (`.sbom.yml`)
5. Default Variables

### 1.2. Supported Configuration Sources

- [x] Command-Line Flags
- [x] Environment Variables (Env Vars)
- [x] Dotenv Files (`.env`)
- [x] Config Files (`.sbom.yml`)
- [x] Default Variables

### 1.3. Examples and Explanation

- Command-line Flags (CLI)
  > Command-line flags have the highest precedence and will override any other configuration source.

  ```bash
  sbom upload --api-url https://api.example.com --api-key KEY \
              --file sbom.cdx.json --auto-create \
              --project-name MyApp --project-version 1.0.0
  ```

  ```bash
  sbom delete --api-url https://api.example.com --api-key KEY \
              --project-name MyApp --project-version 1.0.0
  ```

- Env Vars
  > Environment variables have the second-highest precedence and will override settings from dotenv files, config files, and default variables.

  ```bash
  export SBOM_API_URL="https://api.example.com"
  export SBOM_API_KEY="KEY"

  sbom upload -f sbom.cdx.json
  ```

- DotEnv Files (`.env`)
  > Dotenv files have lower precedence than environment variables and command-line flags but will override config files and default variables.

  ```env
  SBOM_API_URL=https://api.component-analysis.localhost/
  SBOM_API_KEY=<API_KEY>
  SBOM_VERIFY_SSL=true
  SBOM_PARENT_NAME="Project"
  SBOM_PROJECT_NAME="Dependency-Track"
  SBOM_PROJECT_VERSION="4.13.2"
  SBOM_IS_LATEST=true
  SBOM_AUTO_CREATE=true
  ```

  ```bash
  # Explicitly load a trusted dotenv file
  sbom --env-file .env upload -f sbom.cdx.json
  ```

  ```bash
  # Explicitly load a trusted dotenv file
  sbom --env-file .env.stage upload -f sbom.cdx.json
  ```

- Project Configuration (`.sbom.yml`)
  > Run the CLI from the project root to automatically load its `.sbom.yml`.
  >
  > Config files are read in the order: `/etc/sbom/config.yml`, `~/.sbom/config.yml`, then `.sbom.yml`, later files override earlier ones. CLI flags and environment variables override config files. Dotenv loading still requires `--env-file`.

  ```yaml
  api-url: https://api.example.com
  api-key: YOUR_API_KEY
  verify-ssl: true
  project-name: MyApp
  project-version: 1.0.0
  ```

  ```bash
  cd /path/to/project
  sbom upload --file sbom.cdx.json
  sbom delete
  ```

### 1.4. Table of Comparison

| Library        | CLI Flags | Env Vars | DotEnv Files | Config Files | Defaults | Native Precedence | Notes                     |
| -------------- | --------- | -------- | ------------ | ------------ | -------- | ----------------- | ------------------------- |
| Click          | &check;   | &check;  | &cross;      | Custom       | &check;  | Partial           | Config file via user code |
| Typer          | &check;   | &check;  | &cross;      | Custom       | &check;  | Partial           | Built on Click            |
| argparse       | &check;   | Custom   | &cross;      | Custom       | &check;  | Custom            | Standard library          |
| python-fire    | &check;   | Custom   | &cross;      | Custom       | &check;  | Custom            | Auto CLI generation       |
| configargparse | &check;   | &check;  | &check;      | &check;      | &check;  | &check;           | Explicit, recommended     |
| Hydra          | &check;   | Limited  | &cross;      | &check;      | &check;  | &check;           | Hierarchical configs      |
| dynaconf       | &check;   | &check;  | &cross;      | &check;      | &check;  | &check;           | Full-stack config mgmt    |

## 2. References

- [Command Line Interface (CLI)](https://clig.dev/) guide.
- [Click](https://click.palletsprojects.com/) documentation.
- [Typer](https://typer.tiangolo.com/) documentation.
- [argparse](https://docs.python.org/3/library/argparse.html) documentation.
- [python-fire](https://github.com/google/python-fire) documentation.
- [configargparse](https://github.com/bw2/ConfigArgParse) documentation.
- [Hydra](https://hydra.cc/docs/intro/) documentation.
- [dynaconf](https://www.dynaconf.com/) documentation.

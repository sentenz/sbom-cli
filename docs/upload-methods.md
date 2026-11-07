# Upload Methods

Upload a CycloneDX SBOM to Dependency-Track from a local Python installation, a container, or a CI pipeline. Replace `https://dependency-track.example.com` with the HTTPS base URL of the Dependency-Track API as seen from the environment running the CLI.

> [!NOTE]
> Use an API key with `BOM_UPLOAD` and add `PROJECT_CREATION_UPLOAD` when using `--auto-create`. Inject `SBOM_API_KEY` from a secret store or keep it in a trusted, untracked dotenv file.

> [!IMPORTANT]
> TLS certificate verification is enabled by default. Use an API endpoint with a certificate trusted by the CLI runtime. The CLI rejects HTTP redirects, so configure the API base URL that serves upload requests directly.

- [1. Python CLI](#1-python-cli)
  - [1.1. Dotenv File](#11-dotenv-file)
  - [1.2. Command-Line Arguments](#12-command-line-arguments)
  - [1.3. Environment Variables](#13-environment-variables)
  - [1.4. Module Execution](#14-module-execution)
  - [1.5. Config File](#15-config-file)
- [2. Containerized CLI](#2-containerized-cli)
  - [2.1. Dotenv File](#21-dotenv-file)
  - [2.2. Environment Variables](#22-environment-variables)
  - [2.3. Docker Compose](#23-docker-compose)
  - [2.4. Make Task](#24-make-task)
- [3. Upload Patterns](#3-upload-patterns)
  - [3.1. Upload to a new project](#31-upload-to-a-new-project)
  - [3.2. Upload to an existing project](#32-upload-to-an-existing-project)
  - [3.3. Set project metadata](#33-set-project-metadata)
- [4. References](#4-references)

## 1. Python CLI

### 1.1. Dotenv File

Load a trusted file explicitly by placing `--env-file` before `upload`. The CLI loads dotenv settings only when this option is supplied. Existing environment variables take precedence over values in the file.

- `.env`

  ```dotenv
  SBOM_API_URL=https://dependency-track.example.com
  SBOM_API_KEY=replace-with-a-dependency-track-api-key
  SBOM_PROJECT_NAME=MyProject
  SBOM_PROJECT_VERSION=1.0.0
  SBOM_AUTO_CREATE=true
  ```

- Invoke

  ```bash
  sbom --env-file .env upload -f logs/sbom/sbom-image.cdx.json
  ```

### 1.2. Command-Line Arguments

Set `SBOM_API_KEY` in the process environment before running the command. Pass the API URL and project metadata as flags.

- Invoke

  ```bash
  sbom upload \
    -f logs/sbom/sbom-image.cdx.json \
    --api-url https://dependency-track.example.com \
    --verify-ssl \
    --auto-create \
    --project-name "MyProject" \
    --project-version "1.0.0"
  ```

> [!NOTE]
> The TLS flags `--verify-ssl` and `--no-verify-ssl` take no value. Reserve `--no-verify-ssl` or `SBOM_VERIFY_SSL=false` for isolated local testing. The CLI logs a warning when verification is disabled.

### 1.3. Environment Variables

Export the upload settings and supply `SBOM_API_KEY` through the environment, for example as a CI secret.

- Invoke

  ```bash
  export SBOM_API_URL=https://dependency-track.example.com
  export SBOM_PROJECT_NAME="MyProject"
  export SBOM_PROJECT_VERSION="1.0.0"
  export SBOM_AUTO_CREATE=true

  sbom upload -f logs/sbom/sbom-image.cdx.json
  ```

### 1.4. Module Execution

Invoke the CLI module with a trusted dotenv file.

- Invoke

  ```bash
  python -m sbom.cli --env-file .env upload -f logs/sbom/sbom-image.cdx.json
  ```

### 1.5. Config File

Save `.sbom.yml` in a trusted project directory. The CLI automatically reads this file from the current working directory when running `upload`. Supply `SBOM_API_KEY` through the environment.

- `.sbom.yml`

  ```yaml
  api-url: https://dependency-track.example.com
  verify-ssl: true
  project-name: MyProject
  project-version: "1.0.0"
  auto-create: true
  ```

- Invoke

  ```bash
  cd /path/to/project
  sbom upload -f logs/sbom/sbom-image.cdx.json
  ```

> [!NOTE]
> Configuration files are read in [configuration precedence](order-of-precedence.md) from `/etc/sbom/config.yml`, `~/.sbom/config.yml`, and `.sbom.yml`, with later files taking precedence. Command-line flags, environment variables, and explicitly loaded dotenv values override configuration-file settings.

## 2. Containerized CLI

Build the `sbom:latest` image from the repository root before running these examples. Use an API hostname reachable from inside the container.

- Invoke

  ```bash
  make container-docker-build CONTAINER_IMAGE=sbom CONTAINER_TAG=latest
  ```

### 2.1. Dotenv File

Docker reads the trusted `.env` file and passes its values into the container. Docker's `--env-file` appears before the image name. The CLI's `--env-file` appears after the image name and takes a path inside the container.

- Invoke

  ```bash
  docker run --rm \
    --env-file .env \
    -v "$(pwd)/logs/sbom:/workspace/sbom:ro" \
    sbom:latest \
    upload -f /workspace/sbom/sbom-image.cdx.json
  ```

### 2.2. Environment Variables

Export `SBOM_API_KEY` in the calling shell. Docker's `-e SBOM_API_KEY` forwards the value by name.

- Invoke

  ```bash
  docker run --rm \
    -e SBOM_API_URL=https://dependency-track.example.com \
    -e SBOM_API_KEY \
    -e SBOM_PROJECT_NAME="Docker-Project" \
    -e SBOM_PROJECT_VERSION="1.0.0" \
    -e SBOM_AUTO_CREATE=true \
    -v "$(pwd)/logs/sbom:/workspace/sbom:ro" \
    sbom:latest \
    upload -f /workspace/sbom/sbom-image.cdx.json
  ```

### 2.3. Docker Compose

Export `SBOM_API_KEY` before invoking Compose. Save the service definition in `compose.yaml`.

- `compose.yaml`

  ```yaml
  services:
    sbom:
      image: sbom:latest
      environment:
        SBOM_API_URL: https://dependency-track.example.com
        SBOM_API_KEY: "${SBOM_API_KEY:?Set SBOM_API_KEY}"
        SBOM_PROJECT_NAME: docker-compose-project
        SBOM_PROJECT_VERSION: "1.0.0"
        SBOM_AUTO_CREATE: "true"
      volumes:
        - ./logs/sbom:/workspace/sbom:ro
      command:
        - upload
        - -f
        - /workspace/sbom/sbom-image.cdx.json
  ```

- Invoke

  ```bash
  docker compose run --rm sbom
  ```

### 2.4. Make Task

Use `sbom-upload` with a trusted dotenv file and the locally built image. The target passes `--env-file` to the CLI inside the container and writes the output to `logs/sbom/upload.log`.

- Invoke

  ```bash
  make sbom-upload \
    SBOM_CONTAINER_IMAGE=sbom:latest \
    SBOM_FILE_ENV=.env \
    SBOM_FILE_CDX=logs/sbom/sbom-image.cdx.json
  ```

To use the environment variables from [section 1.3](#13-environment-variables), including the injected API key, run `container-docker-run`.

- Invoke

  ```bash
  make container-docker-run CONTAINER_IMAGE=sbom CONTAINER_TAG=latest \
    ARGS="upload -f logs/sbom/sbom-image.cdx.json"
  ```

## 3. Upload Patterns

> [!NOTE]
> The examples assume `SBOM_API_URL` and `SBOM_API_KEY` are already available in the environment.

### 3.1. Upload to a new project

Supply both the project name and version with `--auto-create`.

- Invoke

  ```bash
  sbom upload \
    -f logs/sbom/sbom-image.cdx.json \
    --auto-create \
    --project-name "MyProject" \
    --project-version "1.0.0"
  ```

### 3.2. Upload to an existing project

Use the existing project's exact name and version. Ensure `SBOM_AUTO_CREATE` and `auto-create` in YAML configuration are unset or disabled for this upload.

- Invoke

  ```bash
  sbom upload \
    -f logs/sbom/sbom-image.cdx.json \
    --project-name "MyProject" \
    --project-version "1.0.0"
  ```

### 3.3. Set project metadata

Add a custom project name, version, and tags to group uploaded SBOMs by application or environment.

- Invoke

  ```bash
  sbom upload -f logs/sbom/sbom-image.cdx.json \
    --auto-create \
    --project-name "MyApp" \
    --project-version "2.1.0" \
    --project-tags "production,security"
  ```

## 4. References

- SBOM CLI [configuration precedence](order-of-precedence.md) settings interact.

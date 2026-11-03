# Upload Methods

The SBOM CLI can upload a CycloneDX file to Dependency-Track using several entry points.

> [!NOTE]
> Keep the upload command consistent across local development, CI pipelines, and container-based workflows.

- [1. Python CLI](#1-python-cli)
  - [1.1. Dotenv File](#11-dotenv-file)
  - [1.2. Command-Line Arguments](#12-command-line-arguments)
  - [1.3. Environment Variables](#13-environment-variables)
  - [1.4. Module Execution](#14-module-execution)
  - [1.5. Make Task](#15-make-task)
- [2. Containerized CLI](#2-containerized-cli)
  - [2.1. Dotenv File](#21-dotenv-file)
  - [2.2. Environment Variables](#22-environment-variables)
  - [2.3. Docker Compose](#23-docker-compose)
  - [2.4. Make Task](#24-make-task)
- [3. Upload Patterns](#3-upload-patterns)
  - [3.1. Upload to a new project](#31-upload-to-a-new-project)
  - [3.2. Upload to an existing project](#32-upload-to-an-existing-project)
  - [3.3. Set project metadata](#33-set-project-metadata)

## 1. Python CLI

### 1.1. Dotenv File

```bash
source .env
sbom upload -f logs/sbom/sbom-image.cdx.json
```

### 1.2. Command-Line Arguments

```bash
sbom upload \
  -f logs/sbom/sbom-image.cdx.json \
  --api-url https://dependency-track.localhost \
  --api-key YOUR_API_KEY \
  --verify-ssl false \
  --auto-create \
  --project-name "MyProject" \
  --project-version "1.0.0"
```

### 1.3. Environment Variables

```bash
export SBOM_API_URL=https://dependency-track.localhost
export SBOM_API_KEY=YOUR_API_KEY
export SBOM_VERIFY_SSL=false
export SBOM_PROJECT_NAME="MyProject"
export SBOM_PROJECT_VERSION="1.0.0"
export SBOM_AUTO_CREATE=true

sbom upload -f logs/sbom/sbom-image.cdx.json
```

### 1.4. Module Execution

Invoke the package as a Python module using the `-m` flag.

```bash
python -m sbom upload \
  -f logs/sbom/sbom-image.cdx.json \
  --auto-create \
  --project-name "MyProject" \
  --project-version "1.0.0"
```

### 1.5. Make Task

```bash
make upload-sbom logs/sbom/sbom-image.cdx.json
```

## 2. Containerized CLI

### 2.1. Dotenv File

```bash
docker run --rm \
  --env-file .env \
  -v "$(pwd)/logs/sbom:/workspace/sbom:ro" \
  sbom:latest \
  upload -f /workspace/sbom/sbom-image.cdx.json \
  --auto-create
```

### 2.2. Environment Variables

```bash
docker run --rm \
  -e SBOM_API_URL=https://dependency-track.localhost \
  -e SBOM_API_KEY=YOUR_API_KEY \
  -e SBOM_VERIFY_SSL=false \
  -e SBOM_PROJECT_NAME="Docker-Project" \
  -e SBOM_PROJECT_VERSION="1.0.0" \
  -e SBOM_AUTO_CREATE=true \
  -v "$(pwd)/logs/sbom:/workspace/sbom:ro" \
  sbom:latest \
  upload -f /workspace/sbom/sbom-image.cdx.json
```

### 2.3. Docker Compose

- Compose

  ```yaml
  services:
    sbom:
      image: sbom:latest
      environment:
        SBOM_API_URL: https://dependency-track.localhost
        SBOM_API_KEY: YOUR_API_KEY
        SBOM_VERIFY_SSL: "false"
        SBOM_PROJECT_NAME: docker-compose-project
        SBOM_PROJECT_VERSION: 1.0.0
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

```bash
# Build container once
make container-docker-build

# Upload an SBOM using the containerized CLI
make container-docker-run ARGS="upload -f logs/sbom/sbom-image.cdx.json --auto-create"
```

## 3. Upload Patterns

### 3.1. Upload to a new project

This creates the project automatically when `--auto-create` is set.

```bash
source .env
sbom upload -f logs/sbom/sbom-image.cdx.json --auto-create
```

### 3.2. Upload to an existing project

Use the project UUID when the project already exists.

```bash
sbom upload \
  -f logs/sbom/sbom-image.cdx.json \
  --project-uuid "51cef167-a636-4471-ba41-ae92a7a75e7e"
```

### 3.3. Set project metadata

Add a custom project name, version, and tags to group uploaded SBOMs by application or environment.

```bash
sbom upload -f sbom.json \
  --auto-create \
  --project-name "MyApp" \
  --project-version "2.1.0" \
  --project-tags "production,security"
```

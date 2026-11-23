# syntax=docker/dockerfile:1.29@sha256:572cebbc2b15e6f84c077742952674889cb63cd5e9b80abdffcbe587b6f19183
# SPDX-License-Identifier: Apache-2.0

# =============================================================================
# SBOM CLI — Containerized CLI
#
# Multi-stage build that produces a small, secure runtime image exposing the
# `sbom` command. Build-time tooling (pip, compilers, build deps) is kept in
# the builder stage and never shipped in the final image.
#
#   Build:  docker build -t sbom:latest .
#   Run:    docker run --rm -it \
#              -e SBOM_API_URL=https://api.example.com \
#              -e SBOM_API_KEY=KEY \
#              -v "$PWD/sbom.cdx.json:/workspace/sbom.cdx.json:ro" \
#              sbom:latest upload -f /workspace/sbom.cdx.json
# =============================================================================

FROM python:3.15-slim@sha256:65a65fc7b30b06cb6df4930fd4650697cb23f4c2698ab81fc87e4b031bc36928 AS builder

# Prevent Python from writing .pyc files and enable unbuffered, deterministic
# output. PIP_NO_CACHE_DIR keeps the build context lean.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install build-time system dependencies (needed only to build wheels).
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build

# Install dependencies first to maximize layer caching. Copy only the
# packaging metadata so this layer is invalidated only when dependencies
# change, not on every source edit.
COPY pyproject.toml README.md ./
COPY src ./src

# Install the package (and its runtime dependencies) into an isolated prefix.
RUN python -m pip install --prefix=/install --no-warn-script-location .

FROM python:3.15-slim@sha256:65a65fc7b30b06cb6df4930fd4650697cb23f4c2698ab81fc87e4b031bc36928 AS runtime

LABEL org.opencontainers.image.title="SBOM CLI" \
    org.opencontainers.image.description="Containerized CLI for SBOM operations against a Dependency-Track API server" \
    org.opencontainers.image.source="https://github.com/sentenz/sbom-cli" \
    org.opencontainers.image.documentation="https://github.com/sentenz/sbom-cli/blob/main/README.md" \
    org.opencontainers.image.licenses="Apache-2.0" \
    org.opencontainers.image.vendor="sentenz"

# Runtime environment.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HOME=/home/sbom

ARG USER_GID=10001
ARG USER_UID=10001

# Create a dedicated non-root user and a writable working directory.
RUN groupadd --system --gid "${USER_GID}" sbom \
    && useradd --system --uid "${USER_UID}" --gid sbom --home-dir "${HOME}" --shell /usr/sbin/nologin sbom \
    && mkdir -p "${HOME}" /workspace \
    && chown -R "${USER_UID}:${USER_GID}" "${HOME}" /workspace \
    && chmod 0750 "${HOME}" \
    && chmod 0755 /workspace

# Copy only the installed artifacts (site-packages + console scripts) from the
# builder stage. Build tooling and source are intentionally left behind.
COPY --from=builder --link /install /install

# Relocate the installed packages into the runtime's standard site-packages
# (computed dynamically so the image is robust to the Python version) and put
# the `sbom` console script on PATH. Then drop the temporary install prefix.
RUN set -eux; \
    SP="$(python -c 'import site; print(site.getsitepackages()[0])')"; \
    SRC="$(ls -d /install/lib/python3*/site-packages)"; \
    cp -r "${SRC}"/. "${SP}"/; \
    cp /install/bin/sbom /usr/local/bin/sbom; \
    rm -rf /install

# Drop to the unprivileged user.
USER ${USER_UID}:${USER_GID}

WORKDIR /workspace

# The CLI reads configuration from environment variables (SBOM_API_URL,
# SBOM_API_KEY, ...) and optional .env files. No secrets are baked into the
# image — supply them at runtime.
ENTRYPOINT ["sbom"]

# Default to help output; override with a subcommand, e.g. `upload -f ...`.
CMD ["--help"]

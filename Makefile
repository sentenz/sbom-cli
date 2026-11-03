# SPDX-License-Identifier: Apache-2.0

# Load Dotenv Files

DOTENV_FILES := $(filter-out %.enc,$(wildcard .env .env.*))
ifneq ($(strip $(DOTENV_FILES)),)
	include $(DOTENV_FILES)
	export
endif

# Define Variables

SHELL := bash
.SHELLFLAGS := -euo pipefail -c
.ONESHELL:

PYTHON_VENV := .venv
SBOM_CLI := $(PYTHON_VENV)/bin/sbom

# ─── General ─────────────────────────────────────────────────────────────────────────────────────

default: help

# NOTE Targets MUST have a leading comment line starting with `##` to be included in the list. See the targets below for examples.
#
## Display help message with a list of available tasks and their descriptions
help:
	@awk 'BEGIN {printf "Tasks\n\tA collection of tasks used in the current project.\n\n"}'
	@awk 'BEGIN {printf "Usage\n\tmake $(shell tput -Txterm setaf 6)<task>$(shell tput -Txterm sgr0)\n\n"}' $(MAKEFILE_LIST)
	@awk '/^##/{c=substr($$0,3);next}c&&/^[[:alpha:]][[:alnum:]_-]+:/{print "$(shell tput -Txterm setaf 6)\t" substr($$1,1,index($$1,":")) "$(shell tput -Txterm sgr0)",c}1{c=0}' $(MAKEFILE_LIST) | column -s: -t
.PHONY: help

# ─── Setup & Teardown ────────────────────────────────────────────────────────────────────────────

# Usage: make python-venv-setup <path>
#
# Provision a dedicated Python virtual environment
python-venv-setup:
	@if [ -z "$(filter-out $@,$(MAKECMDGOALS))" ]; then \
		echo "Usage: make python-venv-setup <path>"; \
		exit 1; \
	fi
	@python3 -m venv "$(filter-out $@,$(MAKECMDGOALS))"
.PHONY: python-venv-setup

# Usage: make python-venv-activate <path>
#
# Load the Python virtual environment into the current shell session
python-venv-activate:
	@if [ -z "$(filter-out $@,$(MAKECMDGOALS))" ]; then \
		echo "Usage: make python-venv-activate <path>"; \
		exit 1; \
	fi
	source "$(filter-out $@,$(MAKECMDGOALS))/bin/activate"
.PHONY: python-venv-activate

# Decommission and remove the Python virtual environment, restoring the host state
python-venv-deactivate:
	deactivate
.PHONY: python-venv-deactivate

## Initialize a software development workspace with requisites
bootstrap:
	cd scripts/ && ./bootstrap.sh
.PHONY: bootstrap

## Install and configure all dependencies essential for development
setup:
	@$(MAKE) -s python-venv-setup ".venv"
.PHONY: setup

## Remove development artifacts and restore the host to its pre-setup state
teardown:
	cd scripts/ && ./teardown.sh
.PHONY: teardown

# ─── Dependency Manager ──────────────────────────────────────────────────────────────────────────

## Install the project package into the active environment
pkg-python-install:
	@$(PYTHON_VENV)/bin/python -m pip install --quiet -e ".[dev]"
.PHONY: pkg-python-install

## Uninstall the project package and its dependencies
pkg-python-uninstall:
	@$(PYTHON_VENV)/bin/python -m pip uninstall -y sbom configargparse requests urllib3 python-dotenv
.PHONY: pkg-python-uninstall

# ─── SBOM API ────────────────────────────────────────────────────────────────────────────────────

# Usage: make sbom-upload <file>
#
## Upload a CycloneDX SBOM file to the API server (Python CLI)
sbom-cli-upload:
	@if [ -z "$(filter-out $@,$(MAKECMDGOALS))" ]; then \
		echo "usage: make sbom-upload <file>"; \
		exit 1; \
	fi

	@for file in $(filter-out $@,$(MAKECMDGOALS)); do \
		if [ -f "$$file" ]; then \
			$(SBOM_CLI) upload -f "$$file"; \
		else \
			echo "Skipping (not found): $$file" >&2; \
		fi; \
	done
.PHONY: sbom-cli-upload

## Delete the specified project (and its SBOM) from the API server
sbom-cli-delete:
	@$(SBOM_CLI) delete
.PHONY: sbom-cli-delete

# ─── Analysis ────────────────────────────────────────────────────────────────────────────────────

# Verify that imports are sorted according to isort rules
lint-isort-check:
	isort --check-only src/sbom tests
.PHONY: lint-isort-check

## Automatically sort imports in source and test directories
lint-isort-fix:
	isort src/sbom tests
.PHONY: lint-isort-fix

## Run ruff to detect style violations and potential bugs
lint-ruff-check:
	ruff check src/sbom tests
.PHONY: lint-ruff-check

## Perform static type checking with mypy on source code
lint-mypy-check:
	mypy src/sbom
.PHONY: lint-mypy-check

# ─── Testing ─────────────────────────────────────────────────────────────────────────────────────

TEST_VENV ?= .venv
TEST_PYTEST ?= $(TEST_VENV)/bin/pytest
TEST_REPORT_DIR ?= logs
TEST_PYTEST_TARGETS ?= $(foreach dir,tests/unit tests/fuzz tests/integration tests/e2e,$(if $(wildcard $(dir)),$(dir)))
TEST_PYTEST_COVERAGE_ARGS ?= --junitxml=$(TEST_REPORT_DIR)/junit.xml --cov=sbom --cov-report=term-missing --cov-report=html:$(TEST_REPORT_DIR)/coverage --cov-report=xml:$(TEST_REPORT_DIR)/coverage.xml

## Provision the venv, install the package (editable) with dev tooling
test-setup: setup
	@$(TEST_VENV)/bin/python -m pip install --quiet -e ".[dev]"
.PHONY: test-setup

test-teardown:
	@$(TEST_VENV)/bin/python -m pip uninstall -y sbom configargparse requests urllib3 python-dotenv
.PHONY: test-teardown

## Run the unit test suite
test-unit:
	$(TEST_PYTEST) tests/unit -v
.PHONY: test-unit

## Run the property-based (fuzz) test suite
test-fuzz:
	$(TEST_PYTEST) tests/fuzz -v
.PHONY: test-fuzz

## Run the integration test suite (no-op if empty)
test-integration:
	$(TEST_PYTEST) tests/integration -v || [ $$? -eq 5 ]
.PHONY: test-integration

## Run the end-to-end test suite (requires a live server; no-op if empty)
test-e2e:
	$(TEST_PYTEST) tests/e2e -v || [ $$? -eq 5 ]
.PHONY: test-e2e

## Run the full test suite with a coverage report
test-coverage:
	@mkdir -p $(TEST_REPORT_DIR)
	$(TEST_PYTEST) $(TEST_PYTEST_TARGETS) $(TEST_PYTEST_COVERAGE_ARGS)
.PHONY: test-coverage

## Run the full test suite and fail if coverage drops below the threshold
test-coverage-check:
	$(TEST_PYTEST) $(TEST_PYTEST_TARGETS) $(TEST_PYTEST_COVERAGE_ARGS) --cov-fail-under=80
.PHONY: test-coverage-check

## Run the full test suite with coverage
test: test-setup test-coverage
.PHONY: test

# ─── Skills Manager ──────────────────────────────────────────────────────────────────────────────

## Provision new Agent Skills into the project environment
agent-skills-add:
	DISABLE_TELEMETRY=1 \
	npx skills@1.5.15 add sentenz/skills
.PHONY: agent-skills-add

## Synchronize and update existing Agent Skills in the project environment
agent-skills-update:
	DISABLE_TELEMETRY=1 \
	npx skills@1.5.15 update sentenz/skills \
		--skill multi-stage-dockerfile \
		--skill python-benchmark-testing \
		--skill python-fuzz-testing \
		--skill python-mock-testing \
		--skill python-unit-testing \
		--skill security-audit \
		--skill dependabot \
		--skill github-actions-efficiency \
		--skill github-actions-hardening \
		--skill google-python-style-guide \
		-y
.PHONY: agent-skills-update

# ─── Secrets Manager ─────────────────────────────────────────────────────────────────────────────

SECRETS_SOPS_IMAGE ?= ghcr.io/getsops/sops:v3.13.3@sha256:857f5a151ac0b2bfc55c1e4e5581d66fb8e268e4d106b38e74191f3bac9d58ea
SECRETS_SOPS_ALIAS ?= docker run --rm -v "${PWD}:/workspace" -v "$${HOME}/.gnupg:/root/.gnupg" -w /workspace "$(SECRETS_SOPS_IMAGE)"
SECRETS_SOPS_UID ?= sops-$(notdir $(CURDIR))

# Usage: make secrets-gpg-generate SECRETS_SOPS_UID=<uid>
#
## Generate a new GPG key pair for SOPS with the specified UID
secrets-gpg-generate:
	@gpg --batch --quiet --passphrase '' --quick-generate-key "$(SECRETS_SOPS_UID)" ed25519 cert,sign 0
	@NEW_FPR="$$(gpg --list-keys --with-colons "$(SECRETS_SOPS_UID)" | awk -F: '/^fpr:/ {print $$10; exit}')"
	@gpg --batch --quiet --passphrase '' --quick-add-key "$${NEW_FPR}" cv25519 encrypt 0
.PHONY: secrets-gpg-generate

# Usage: make secrets-gpg-export SECRETS_SOPS_UID=<uid>
#
## Export the GPG key pair for SOPS with the specified UID to ASCII files
secrets-gpg-export:
	@if [ -z "$(SECRETS_SOPS_UID)" ]; then \
		echo "usage: make secrets-gpg-export SECRETS_SOPS_UID=<uid>" >&2; \
		exit 1; \
	fi

	@gpg --armor --export "$(SECRETS_SOPS_UID)" > "$(SECRETS_SOPS_UID)-public.asc"
	@gpg --armor --export-secret-keys "$(SECRETS_SOPS_UID)" > "$(SECRETS_SOPS_UID)-private.asc"
.PHONY: secrets-gpg-export

# Usage: make secrets-gpg-import [SECRETS_SOPS_UID=<uid>] <key-files>
#
## Import GPG keys from specified files and if provided set ultimate trust for the SOPS UID
secrets-gpg-import:
	@if [ -z "$(filter-out $@,$(MAKECMDGOALS))" ]; then \
		echo "usage: make secrets-gpg-import <files>" >&2; \
		exit 1; \
	fi

	# Import keys from specified files
	@for file in $(filter-out $@,$(MAKECMDGOALS)); do \
		if [ -f "$$file" ]; then \
			gpg --import "$$file"; \
		fi; \
	done

	# Set ultimate trust for the SECRETS_SOPS_UID
	@if [ "$(origin SECRETS_SOPS_UID)" = "command line" ] && [ -n "$(SECRETS_SOPS_UID)" ]; then \
		FPR="$$( { gpg --list-keys --with-colons "$(SECRETS_SOPS_UID)" 2>/dev/null || true; } | awk -F: '/^fpr:/ {print $$10; exit}')"; \
		if [ -n "$${FPR}" ]; then \
			echo "$${FPR}:6:" | gpg --import-ownertrust; \
		fi; \
	fi
.PHONY: secrets-gpg-import

# Usage: make secrets-gpg-remove SECRETS_SOPS_UID=<uid>
#
## Remove GPG keys for SOPS with the specified UID (interactive)
secrets-gpg-remove:
	@if ! gpg --list-keys "$(SECRETS_SOPS_UID)" >/dev/null 2>&1; then
		echo "warning: no key found for '$(SECRETS_SOPS_UID)'" >&2
		exit 0
	fi

	# Delete private key first, then public key
	@gpg --yes --delete-secret-keys "$(SECRETS_SOPS_UID)"
	@gpg --yes --delete-keys "$(SECRETS_SOPS_UID)"
.PHONY: secrets-gpg-remove

# Usage: make secrets-gpg-show [SECRETS_SOPS_UID=<uid>]
#
## Show GPG public key information for SOPS UID or list all keys if UID is not set
secrets-gpg-show:
	@if [ "$(origin SECRETS_SOPS_UID)" != "command line" ]; then \
		gpg --list-keys --keyid-format long; \
		exit 0; \
	fi

	@FPR="$$( { gpg --list-keys --with-colons "$(SECRETS_SOPS_UID)" 2>/dev/null || true; } | awk -F: '/^fpr:/ {print $$10; exit}')"; \
	if [ -z "$${FPR}" ]; then \
		echo "error: no fingerprint found for UID '$(SECRETS_SOPS_UID)'" >&2; \
		exit 1; \
	fi; \
	echo -e "UID: $(SECRETS_SOPS_UID)\nFingerprint: $${FPR}"
.PHONY: secrets-gpg-show

# Usage: make secrets-sops-encrypt <files>
#
## Encrypt specified files using SOPS with GPG keys, writing output to <file>.enc
secrets-sops-encrypt:
	@if [ -z "$(filter-out $@,$(MAKECMDGOALS))" ]; then \
		echo "usage: make secrets-sops-encrypt <files>" >&2; \
		exit 1; \
	fi

	@for file in $(filter-out $@,$(MAKECMDGOALS)); do \
		if [ -f "$$file" ]; then \
			$(SECRETS_SOPS_ALIAS) encrypt --output "$$file.enc" "$$file"; \
		else \
			echo "file not found: $$file" >&2; \
		fi; \
	done
.PHONY: secrets-sops-encrypt

# Usage: make secrets-sops-decrypt <files>
#
## Decrypt specified SOPS-encrypted files (expects <file>.enc), writing output to <file>
secrets-sops-decrypt:
	@if [ -z "$(filter-out $@,$(MAKECMDGOALS))" ]; then \
		echo "usage: make secrets-sops-decrypt <files>" >&2; \
		exit 1; \
	fi

	@for file in $(filter-out $@,$(MAKECMDGOALS)); do \
		case "$$file" in \
			*.enc) \
				$(SECRETS_SOPS_ALIAS) decrypt --filename-override "$${file%.enc}" --output "$${file%.enc}" "$$file"; \
				;;
			*) \
				$(SECRETS_SOPS_ALIAS) decrypt --in-place "$$file"; \
				;;
		esac; \
	done
.PHONY: secrets-sops-decrypt

# Usage: make secrets-sops-view <file>
#
## View decrypted contents of a SOPS-encrypted file using GPG keys
secrets-sops-view:
	@if [ -z "$(filter-out $@,$(MAKECMDGOALS))" ]; then \
		echo "usage: make secrets-sops-view <file>" >&2; \
		exit 1; \
	fi

	$(SECRETS_SOPS_ALIAS) decrypt "$(filter-out $@,$(MAKECMDGOALS))"
.PHONY: secrets-sops-view

# ─── Container Manager ───────────────────────────────────────────────────────────────────────────

CONTAINER_IMAGE ?= $(notdir $(shell git rev-parse --show-toplevel 2>/dev/null))
CONTAINER_TAG ?= $(shell awk -F'"' '/^version[[:space:]]*=/ {print $$2}' pyproject.toml)
CONTAINER_DOCKERFILE ?= Dockerfile
CONTAINER_CONTEXT ?= .
CONTAINER_WORKDIR ?= /workspace
SBOM_ENV_VARS ?= SBOM_API_URL SBOM_API_KEY SBOM_VERIFY_SSL SBOM_PROJECT_UUID SBOM_PROJECT_NAME SBOM_PROJECT_VERSION SBOM_PARENT_NAME SBOM_PARENT_VERSION SBOM_PARENT_UUID SBOM_IS_LATEST SBOM_AUTO_CREATE

## Build the containerized SBOM CLI image
container-docker-build:
	docker build \
		--tag "$(CONTAINER_IMAGE):$(CONTAINER_TAG)" \
		--file "$(CONTAINER_DOCKERFILE)" \
		"$(CONTAINER_CONTEXT)"
.PHONY: container-docker-build

# Usage: make container-docker-run ARGS="<subcommand> [args...]"
#
# Example:
#   make container-docker-run ARGS="upload -f sbom.cdx.json"
#   make container-docker-run ARGS="delete --project-name MyApp --project-version 1.0.0"
#
# Required environment variables (set via .env file, env var, or command-line):
#   SBOM_API_URL         - API server URL (e.g., https://api.example.com)
#   SBOM_API_KEY         - API authentication key
#   SBOM_PROJECT_NAME    - Project name in Dependency-Track
#   SBOM_PROJECT_VERSION - Project version
#
## Run the containerized SBOM CLI, forwarding SBOM_* env vars and the workspace
container-docker-run:
	@if [ -z "$(ARGS)" ]; then \
		echo "usage: make container-docker-run ARGS=\"<subcommand> [args...]\""; \
		exit 1; \
	fi

	@API_HOST=""; \
	if [ -n "$${SBOM_API_URL:-}" ]; then \
		API_HOST="$${SBOM_API_URL#*://}"; \
		API_HOST="$${API_HOST%%/*}"; \
		API_HOST="$${API_HOST%%:*}"; \
	fi; \
	HOST_ARGS=""; \
	if printf '%s' "$${API_HOST:-}" | grep -Eq '(^|\.)localhost$$|^127\.0\.0\.1$$'; then \
		HOST_ARGS="--network host"; \
	fi; \
	ENV_ARGS=""; \
	for v in $(SBOM_ENV_VARS); do \
		if [ -n "$${!v:-}" ]; then \
			ENV_VAL="$$(printf '%s' "$${!v}" | tr -d "\"'")"; \
			ENV_ARGS="$$ENV_ARGS -e $$v=$$ENV_VAL"; \
		fi; \
	done; \
	docker run --rm \
		-w "$(CONTAINER_WORKDIR)" \
		-v "$${PWD}:$(CONTAINER_WORKDIR):ro" \
		$$HOST_ARGS \
		$$ENV_ARGS \
		"$(CONTAINER_IMAGE):$(CONTAINER_TAG)" $(ARGS)
.PHONY: container-docker-run

## Remove the containerized SBOM CLI image and any associated containers
container-docker-teardown:
	@docker rm -f "$$(docker ps -aq -f ancestor="$(CONTAINER_IMAGE):$(CONTAINER_TAG)")" 2>/dev/null || true
	@docker rmi "$(CONTAINER_IMAGE):$(CONTAINER_TAG)"
.PHONY: container-docker-teardown

# ─── SBOM Manager ─────────────────────────────────────────────────────────────────────────

SBOM_CONTAINER_IMAGE ?= ghcr.io/sentenz/sbom-cli:v1.0.0
SBOM_CONTAINER_ALIAS := docker run --rm --network=host -v "${PWD}:/workspace" -w /workspace "$(SBOM_CONTAINER_IMAGE)"

SBOM_FILE_ENV ?= .env
SBOM_FILE_CDX ?= logs/sbom/sbom-image.cdx.json

# Usage: make sbom-upload SBOM_FILE_ENV=".env.stage" SBOM_FILE_CDX="logs/sbom/sbom-image.cdx.json"
#
## Upload SBOM to the SCA platform and generate a report
sbom-upload:
	@mkdir -p logs/sbom

	$(SBOM_CONTAINER_ALIAS) --env-file "$(SBOM_FILE_ENV)" upload --file "$(SBOM_FILE_CDX)" 2>&1 | tee logs/sbom/upload.log
.PHONY: sbom-upload

# ─── SAST Manager ────────────────────────────────────────────────────────────────────────────────

SAST_SEMGREP_IMAGE ?= semgrep/semgrep:1.183.0@sha256:2e45517a85e13a9cca14a2a00df6bb48affd66b8ebfae1b0991cd57578362fb0
SAST_SEMGREP_ALIAS := docker run --rm -v "${PWD}:/workspace" -w /workspace "$(SAST_SEMGREP_IMAGE)"
SAST_SEMGREP_FILES ?= .
SAST_SEMGREP_FILTER = $(if $(strip $(SAST_SEMGREP_FILES)),$(SAST_SEMGREP_FILES),.)

## Scan source code for security issues using Semgrep and generate a report
sast-semgrep-scan:
	@mkdir -p logs/sast

	$(SAST_SEMGREP_ALIAS) semgrep scan --config auto --error --json --output logs/sast/semgrep.json $(SAST_SEMGREP_FILTER) 2> logs/sast/semgrep.log
.PHONY: sast-semgrep-scan

SAST_TRIVY_IMAGE ?= aquasec/trivy:0.76.1@sha256:790fd66d1697395d8693d1acaa1ea702406a20f109b6fc7bac8db623eca6c06c
SAST_TRIVY_ALIAS := docker run --rm -v "${PWD}:/workspace" -w /workspace "$(SAST_TRIVY_IMAGE)"
SAST_TRIVY_FILES ?= .

## Scan Infrastructure-as-Code (IaC) files for misconfigurations using Trivy and generate a report
sast-trivy-misconfig:
	@mkdir -p logs/sast

	$(SAST_TRIVY_ALIAS) config --output logs/sast/trivy-misconfig.json $(SAST_TRIVY_FILES) 2>&1
.PHONY: sast-trivy-misconfig

## Scan local filesystem for vulnerabilities and misconfigurations using Trivy
sast-trivy-fs:
	@mkdir -p logs/sast

	$(SAST_TRIVY_ALIAS) filesystem --output logs/sast/trivy-filesystem.json /workspace 2>&1
.PHONY: sast-trivy-fs

# Usage: make sast-trivy-image <image_name>
#
## Scan a container image for vulnerabilities using Trivy
sast-trivy-image:
	@if [ -z "$(filter-out $@,$(MAKECMDGOALS))" ]; then \
		echo "usage: make sast-trivy-image <image_name>"; \
		exit 1; \
	fi

	@mkdir -p logs/sast

	docker run --rm -v /var/run/docker.sock:/var/run/docker.sock -v "${PWD}:/workspace" -w /workspace "$(SAST_TRIVY_IMAGE)" image --output logs/sast/trivy-image.json "$(filter-out $@,$(MAKECMDGOALS))" 2>&1
.PHONY: sast-trivy-image

# Usage: make sast-trivy-image-license <image_name>
#
## Scan a container image for license compliance using Trivy
sast-trivy-image-license:
	@if [ -z "$(filter-out $@,$(MAKECMDGOALS))" ]; then \
		echo "usage: make sast-trivy-image-license <image_name>"; \
		exit 1; \
	fi

	@mkdir -p logs/sast

	$(SAST_TRIVY_ALIAS) image --scanners license --format table --output logs/sast/trivy-image-license.txt "$(filter-out $@,$(MAKECMDGOALS))" 2>&1
.PHONY: sast-trivy-image-license

# Usage: make sast-trivy-repository <repo_url>
#
## Scan a remote repository for vulnerabilities using Trivy
sast-trivy-repository:
	@if [ -z "$(filter-out $@,$(MAKECMDGOALS))" ]; then \
		echo "usage: make sast-trivy-repository <repo_url>"; \
		exit 1; \
	fi

	@mkdir -p logs/sast

	$(SAST_TRIVY_ALIAS) repository --output logs/sast/trivy-repository.json "$(filter-out $@,$(MAKECMDGOALS))" 2>&1
.PHONY: sast-trivy-repository

# Usage: make sast-trivy-rootfs <path>
#
## Scan a rootfs e.g. `/` for vulnerabilities using Trivy
sast-trivy-rootfs:
	@if [ -z "$(filter-out $@,$(MAKECMDGOALS))" ]; then \
		echo "usage: make sast-trivy-rootfs <path>"; \
		exit 1; \
	fi

	@mkdir -p logs/sast

	$(SAST_TRIVY_ALIAS) rootfs --output logs/sast/trivy-rootfs.json "$(filter-out $@,$(MAKECMDGOALS))" 2>&1
.PHONY: sast-trivy-rootfs

# Usage: make sast-trivy-sbom-scan <sbom_path>
#
## Scan SBOM for vulnerabilities using Trivy
sast-trivy-sbom-scan:
	@if [ -z "$(filter-out $@,$(MAKECMDGOALS))" ]; then \
		echo "usage: make sast-trivy-sbom-scan <sbom_path>"; \
		exit 1; \
	fi

	@mkdir -p logs/sast

	$(SAST_TRIVY_ALIAS) sbom --output logs/sast/trivy-sbom.json "$(filter-out $@,$(MAKECMDGOALS))" 2>&1
.PHONY: sast-trivy-sbom-scan

# Usage: make sast-trivy-sbom-cyclonedx-image <image_name>
#
## Generate SBOM in CycloneDX format for a container image using Trivy
sast-trivy-sbom-cyclonedx-image:
	@if [ -z "$(filter-out $@,$(MAKECMDGOALS))" ]; then \
		echo "usage: make sast-trivy-sbom-cyclonedx-image <image_name>"; \
		exit 1; \
	fi

	@mkdir -p logs/sbom

	docker run --rm -v /var/run/docker.sock:/var/run/docker.sock -v "${PWD}:/workspace" -w /workspace "$(SAST_TRIVY_IMAGE)" image --format cyclonedx --output logs/sbom/sbom-image.cdx.json "$(filter-out $@,$(MAKECMDGOALS))" 2>&1
.PHONY: sast-trivy-sbom-cyclonedx-image

# Usage: make sast-trivy-sbom-cyclonedx-fs <path>
#
## Generate SBOM in CycloneDX format for a file system using Trivy
sast-trivy-sbom-cyclonedx-fs:
	@if [ -z "$(filter-out $@,$(MAKECMDGOALS))" ]; then \
		echo "usage: make sast-trivy-sbom-cyclonedx-fs <path>"; \
		exit 1; \
	fi

	@mkdir -p logs/sbom

	$(SAST_TRIVY_ALIAS) filesystem --format cyclonedx --output logs/sbom/sbom-fs.cdx.json "$(filter-out $@,$(MAKECMDGOALS))" 2>&1
.PHONY: sast-trivy-sbom-cyclonedx-fs

# Usage: make sast-trivy-sbom-license <sbom_path>
#
## Scan SBOM for license compliance using Trivy
sast-trivy-sbom-license:
	@if [ -z "$(filter-out $@,$(MAKECMDGOALS))" ]; then \
		echo "usage: make sast-trivy-sbom-license <sbom_path>"; \
		exit 1; \
	fi

	@mkdir -p logs/sast

	$(SAST_TRIVY_ALIAS) sbom --scanners license --format table --output logs/sast/trivy-sbom-license.txt "$(filter-out $@,$(MAKECMDGOALS))" 2>&1
.PHONY: sast-trivy-sbom-license

# Usage: make sast-trivy-sbom-attestation <intoto_sbom_path>
#
## Scan the verified SBOM attestation using Trivy
sast-trivy-sbom-attestation:
	@if [ -z "$(filter-out $@,$(MAKECMDGOALS))" ]; then \
		echo "usage: make sast-trivy-sbom-attestation <intoto_sbom_path>"; \
		exit 1; \
	fi

	@mkdir -p logs/sast

	$(SAST_TRIVY_ALIAS) sbom "$(filter-out $@,$(MAKECMDGOALS))"
.PHONY: sast-trivy-sbom-attestation

# Usage: make sast-trivy-vm <vm_image_path>
#
## [EXPERIMENTAL] Scan a virtual machine image using Trivy
sast-trivy-vm:
	@if [ -z "$(filter-out $@,$(MAKECMDGOALS))" ]; then \
		echo "usage: make sast-trivy-vm <vm_image_path>"; \
		exit 1; \
	fi

	@mkdir -p logs/sast

	$(SAST_TRIVY_ALIAS) vm --output logs/sast/trivy-vm.json "$(filter-out $@,$(MAKECMDGOALS))" 2>&1
.PHONY: sast-trivy-vm

# Usage: make sast-trivy-kubernetes [target]
#
## [EXPERIMENTAL] Scan kubernetes cluster using Trivy (default `cluster`)
sast-trivy-kubernetes:
	@echo "Note: This requires KUBECONFIG to be mounted or available to the container. Assuming ~/.kube/config is mounted to /root/.kube/config"

	@mkdir -p logs/sast

	docker run --rm -v "${HOME}/.kube/config:/root/.kube/config" -v "${PWD}:/workspace" -w /workspace "$(SAST_TRIVY_IMAGE)" kubernetes --output logs/sast/trivy-kubernetes.json $(if $(filter-out $@,$(MAKECMDGOALS)),$(filter-out $@,$(MAKECMDGOALS)),cluster) 2>&1
.PHONY: sast-trivy-kubernetes

SAST_TRIVY_KBOM_FILE ?= logs/sbom/kbom.cdx.json

## Generate a CycloneDX KBOM (Kubernetes Bill of Materials) from the selected Kubernetes cluster
sast-trivy-kbom:
	@test -s "$(K8S_KUBECONFIG)" || { \
		echo "error: kubeconfig not found: $(K8S_KUBECONFIG)" >&2; \
		exit 1; \
	}

	@mkdir -p "$(dir $(SAST_TRIVY_KBOM_FILE))"

	docker run --rm --user root --network host --volume /var/run/docker.sock:/var/run/docker.sock --volume "$(CURDIR):/workspace" --workdir /workspace \
		"$(SAST_TRIVY_IMAGE)" k8s --kubeconfig "$(K8S_KUBECONFIG)" --format cyclonedx --output "/workspace/$(SAST_TRIVY_KBOM_FILE)"
.PHONY: sast-trivy-kbom

SAST_IMAGE_GITLEAKS ?= ghcr.io/gitleaks/gitleaks:v8.30.1@sha256:c00b6bd0aeb3071cbcb79009cb16a60dd9e0a7c60e2be9ab65d25e6bc8abbb7f

## Scan git repository history for leaked secrets using Gitleaks and generate a report
sast-gitleaks-detect:
	@mkdir -p logs/sast

	docker run --rm -v "${PWD}:/workspace" -w /workspace "$(SAST_IMAGE_GITLEAKS)" detect --redact --source /workspace --report-format json --report-path logs/sast/gitleaks-detect.json 2>&1
.PHONY: sast-gitleaks-detect

## Scan staged git changes for leaked secrets using Gitleaks and generate a report
sast-gitleaks-staged:
	@mkdir -p logs/sast

	docker run --rm -v "${PWD}:/workspace" -w /workspace "$(SAST_IMAGE_GITLEAKS)" protect --redact --staged --source /workspace --report-format json --report-path logs/sast/gitleaks-protect.json 2>&1
.PHONY: sast-gitleaks-staged

SAST_IMAGE_TRUFFLEHOG ?= trufflesecurity/trufflehog:3.99.8@sha256:674b2f187620a19df77f44cf9a7d77efcc581a5662accef2f2739cbb46ba4a3a

## Scan local filesystem for leaked secrets using TruffleHog and generate a report
sast-trufflehog-fs:
	@mkdir -p logs/sast

	docker run --rm -v "${PWD}:/workspace" -w /workspace "$(SAST_IMAGE_TRUFFLEHOG)" filesystem . --no-update --json > logs/sast/trufflehog-filesystem.json 2> logs/sast/trufflehog-filesystem.log
.PHONY: sast-trufflehog-fs

## Scan git repository history for leaked secrets using TruffleHog and generate a report
sast-trufflehog-git:
	@mkdir -p logs/sast

	docker run --rm -v "${PWD}:/workspace" -w /workspace "$(SAST_IMAGE_TRUFFLEHOG)" git file:///workspace --no-update --json > logs/sast/trufflehog-git.json 2> logs/sast/trufflehog-git.log
.PHONY: sast-trufflehog-git

#!/bin/bash
#
# Remove development artifacts and restore the host to its pre-setup state.

# -x: print a trace (debug)
# -u: treat unset variables
# -o pipefail: return value of a pipeline
set -uo pipefail

# Include Scripts

source ./../scripts/shell/pkg.sh

# Constant Variables

readonly -A GO_PACKAGES=(
  ["tflint"]=""
  ["sops"]=""
)

readonly -A SNAP_PACKAGES=(
  ["terraform"]=""
  ["terraform-docs"]=""
  ["tflint"]=""
  ["trivy"]=""
)

readonly -A APT_PACKAGES=(
  ["make"]=""
  ["bash"]=""
  ["git"]=""
  ["git-lfs"]=""
  ["gpg"]=""
  ["jq"]=""
  ["python3"]=""
  ["python3-venv"]=""
  ["python3-pip"]=""
  ["cmake"]=""
  ["ninja-build"]=""
  ["ccache"]=""
  ["dos2unix"]=""
  ["srecord"]=""
  ["unzip"]=""
  ["wget"]=""
)

# Control Flow Logic

function teardown() {
  # NOTE Use reversed order of `bootstrap.sh` and `setup.sh` scripts for tearing down the environment

  local -i retval=0

  pkg_go_uninstall_list GO_PACKAGES
  ((retval |= $?))

  pkg_go_clean
  ((retval |= $?))

  pkg_snap_uninstall_list SNAP_PACKAGES
  ((retval |= $?))

  pkg_apt_uninstall_list APT_PACKAGES
  ((retval |= $?))

  pkg_apt_clean
  ((retval |= $?))

  return "${retval}"
}

teardown
exit "${?}"

# SPDX-License-Identifier: Apache-2.0

package tests.policy

import rego.v1

is_pyproject if {
	input.project.dependencies
}

# METADATA
# title: Python runtime dependencies must be pinned
# description: Require exact versions for project runtime dependencies
# custom:
#   severity: medium
# entrypoint: true
deny_unpinned_runtime_dependencies contains msg if {
	is_pyproject
	some dependency in input.project.dependencies
	not regex.match(`^[A-Za-z0-9_.-]+(\[[^]]+\])?==[^ ;]+$`, dependency)
	msg := sprintf("Runtime dependency %q must use an exact == version pin", [dependency])
}

# METADATA
# title: Python development dependencies must be pinned
# description: Require exact versions for project development dependencies
# custom:
#   severity: medium
# entrypoint: true
deny_unpinned_dev_dependencies contains msg if {
	is_pyproject
	some dependency in input.project["optional-dependencies"].dev
	not regex.match(`^[A-Za-z0-9_.-]+(\[[^]]+\])?==[^ ;]+$`, dependency)
	msg := sprintf("Development dependency %q must use an exact == version pin", [dependency])
}

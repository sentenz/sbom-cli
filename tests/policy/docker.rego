# SPDX-License-Identifier: Apache-2.0

package tests.policy

import rego.v1

is_dockerfile if {
	input[0].Cmd
}

# METADATA
# title: Dockerfile base image pinning
# description: Require a digest for each Dockerfile base image
# custom:
#   severity: medium
# entrypoint: true
deny_dockerfile_base_image contains msg if {
	is_dockerfile
	some command in input
	command.Cmd == "from"
	image := command.Value[0]
	not contains(image, "@sha256:")
	msg := sprintf("Dockerfile base image %q must be pinned by digest", [image])
}

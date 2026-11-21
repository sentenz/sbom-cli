# SBOM CLI

The `sbom` command uploads CycloneDX files to OWASP Dependency-Track and deletes projects by UUID or by exact name and version.

## Upload a file

From an installed checkout, inspect the available options with `sbom upload --help`. Set `SBOM_API_KEY` through the process environment, then supply the server and an existing project:

```bash
sbom upload --api-url https://dependency-track.example.com \
  --file sbom.cdx.json --project-name inventory --project-version 1.0.0
```

Add `--auto-create` to create the project if it is missing. The option requires both a name and a version.

## Delete a project

Deletion removes the Dependency-Track project and its SBOM. Set `SBOM_API_URL` and `SBOM_API_KEY`, then select the project with either `--project-uuid` or both `--project-name` and `--project-version`. The two selection methods are mutually exclusive, including values inherited from configuration.

```bash
sbom delete --project-name inventory --project-version 1.0.0
```

## Reference

- [CLI reference](cli.md) lists options, environment variables, config keys, and defaults for each command.
- [Configuration precedence](order-of-precedence.md) traces a setting through the shell, dotenv, and configuration files.
- [Upload methods](upload-methods.md) gives examples for local execution, containers, and CI.

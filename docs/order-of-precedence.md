# Configuration precedence

For each option on `upload` or `delete`, the first source that supplies a value wins. Different options in the same invocation can come from different sources.

| Priority | Source | Example for the project name |
| --- | --- | --- |
| 1 | Command-line option after the command | `--project-name api` |
| 2 | Process environment | `SBOM_PROJECT_NAME=ci` |
| 3 | Dotenv file selected with the root option `--env-file` | `SBOM_PROJECT_NAME=staging` |
| 4 | Configuration file | `project-name: baseline` |
| 5 | Parser default | Project name is unset |

The CLI loads a trusted dotenv file with `python-dotenv` before ConfigArgParse resolves command options. Existing environment variables retain their values. A local `.env` takes effect only when selected explicitly, and the path must identify an existing file.

## Configuration files

For each command, ConfigArgParse reads the following files when present. A later file overrides an earlier file for the same key.

1. `/etc/sbom/config.yml` (system)
2. `~/.sbom/config.yml` (user)
3. `.sbom.yml` in the current working directory (project)

Use flat key-value entries. The [CLI reference](cli.md) lists the keys and environment bindings accepted by each command. Keep shared configuration to keys recognized by every command that will read it. For example, `auto-create` belongs to `upload` and produces an argument error with `delete`.

## Worked example

Save the project settings in `.sbom.yml`.

```yaml
api-url: https://dependency-track.example.com
project-name: baseline
project-version: 1.0.0
```

Set `SBOM_PROJECT_NAME=staging` in `.env.stage`. With a readable CycloneDX file and `SBOM_API_KEY` supplied by the shell or CI secret store, run:

```bash
SBOM_PROJECT_NAME=ci sbom --env-file .env.stage upload \
  --file sbom.cdx.json --project-name api --auto-create
```

This uploads to project `api`, version `1.0.0`. Omitting `--project-name api` selects `ci`. Removing that environment assignment as well selects `staging` if the shell has no exported `SBOM_PROJECT_NAME`. Omitting `--env-file .env.stage` too selects `baseline`.

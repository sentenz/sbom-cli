# Security defaults and migration

TLS certificate verification is enabled by default for upload and delete.
`SBOM_VERIFY_SSL=false` or `--no-verify-ssl` explicitly disables it; use this
only for trusted development endpoints. `--verify-ssl` explicitly enables it
and overrides the environment. Insecure request warnings remain visible.

API redirects are rejected, including redirects to the same host. Configure
`SBOM_API_URL` with the final API base URL so the client never forwards an API
key or SBOM body to a redirect target.

The CLI no longer automatically loads `.env` or `.sbom.yml` from the working
directory. Export environment variables or explicitly select a trusted dotenv
file before the subcommand:

```sh
sbom --env-file /trusted/path/.env upload --file sbom.cdx.json
```

Existing environment variables take precedence over the selected dotenv file;
command-line flags take precedence over both. User and system configuration
paths remain unchanged. Do not select configuration files from an untrusted
checkout: they can choose the endpoint receiving an inherited API key.

Deletion accepts either a UUID or a name/version pair. Conflicting selectors
(including inherited environment settings) are rejected; unset unused selector
variables before running the command. UUIDs are validated and normalized before
being placed in a request path. Name/version lookup requires a unique exact
match in the returned results and rejects malformed or ambiguous responses.
Use an explicit UUID when the server returns ambiguous results. This validation
does not establish server-wide uniqueness across paginated responses or protect
against a compromised server.

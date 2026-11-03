# Troubleshoot

- [1. Common Issues](#1-common-issues)
  - [1.1. File Permission Issues](#11-file-permission-issues)
  - [1.2. Authentication Errors](#12-authentication-errors)
  - [1.3. Connection Refused](#13-connection-refused)
  - [1.4. DNS Resolution Errors](#14-dns-resolution-errors)
- [2. References](#2-references)

## 1. Common Issues

### 1.1. File Permission Issues

Ensure that the SBOM file has the correct permissions and is readable by the user or process running the SBOM CLI.

- Error

  ```plaintext
  `Permission denied` when accessing logs/sbom/sbom-image.cdx.json
  ```

- Solution

  ```bash
  chmod 644 logs/sbom/sbom-image.cdx.json
  ```

### 1.2. Authentication Errors

Ensure that the API key is correctly set in the environment variables and has the necessary permissions.

- Error

  ```plaintext
  HTTP 401 Unauthorized
  ```

- Causes

  - Invalid or expired API key
  - API key doesn't have BOM upload permissions
  - API key doesn't have project creation permissions (if using auto-create)

- Solution

  ```bash
  echo $SBOM_API_KEY
  ```

### 1.3. Connection Refused

Ensure that the Dependency-Track server is running and the hostname is correctly resolvable.

- Error

  ```plaintext
  Failed to connect to dependency-track.localhost port 443
  ```

- Solution

  ```bash
  # Test connectivity
  curl -k https://dependency-track.localhost/api/v1/version

  # Add to /etc/hosts if needed
  echo "127.0.0.1 dependency-track.localhost" | sudo tee -a /etc/hosts
  ```

### 1.4. DNS Resolution Errors

Ensure that the hostname of the Dependency-Track server is resolvable from the network.

- Error

  ```plaintext
  `Name or service not known` when resolving dependency-track.localhost
  ```

- Solution

  ```bash
  # Check /etc/hosts
  cat /etc/hosts | grep dependency-track

  # Add entry if missing
  echo "127.0.0.1 dependency-track.localhost" | sudo tee -a /etc/hosts
  ```

## 2. References

- OWASP [Dependency-Track](https://dependencytrack.github.io/docs) documentation.

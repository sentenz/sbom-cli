"""
SBOM Client for Dependency-Track API

This module provides a client for interacting with the Dependency-Track
API to manage SBOMs. It uses a persistent requests.Session with a retry
strategy for handling transient HTTP errors.
"""

import base64
import json
import os
from uuid import UUID

import requests

from sbom.resources import constants
from sbom.utils import exceptions, http


class Client:
    """Client for interacting with a Dependency-Track API server.

    This client uses a persistent requests.Session with a retry strategy.
    All methods raise custom exceptions to indicate failure. Logging is left
    to the caller.

    Args:
        api_url: Base URL of the Dependency-Track server
            (e.g., "https://dt.example.com").
        api_key: API key for authentication with the Dependency-Track server.
        verify_ssl: Whether to verify TLS certificates. Defaults to True.
        timeout: Request timeout in seconds. Defaults to 30.0.
        session: Optional pre-configured requests.Session. If not provided,
            a retry-enabled session will be created.
    """

    def __init__(
        self,
        api_url: str,
        api_key: str,
        verify_ssl: bool = True,
        timeout: float = constants.DEFAULT_TIMEOUT_SECONDS,
        session: requests.Session | None = None,
    ) -> None:
        if not api_url:
            raise exceptions.ValidationError("`api_url` must be a non-empty string.")
        if not api_key:
            raise exceptions.ValidationError("`api_key` must be a non-empty string.")

        self.base_url: str = api_url.rstrip("/")
        self.api_key: str = api_key
        self.verify_ssl: bool = verify_ssl
        self.timeout: float = timeout
        self.session: requests.Session = session or http.session_retries()
        self.headers: dict[str, str] = {constants.API_KEY_HEADER: self.api_key}

    def _send_request(
        self,
        method: str,
        endpoint: str,
        params: dict[str, str] | None = None,
        data: str | dict | None = None,
        files: dict | None = None,
    ) -> dict:
        """Send an HTTP request to the Dependency-Track API, raising on errors.

        Args:
            method: HTTP method (e.g., "GET", "POST", "DELETE", "PUT").
            endpoint: API endpoint path (e.g., "/api/v1/bom").
            params: URL query parameters for GET requests.
            data: Form data, JSON string, or dict for POST/PUT requests.
                If a string is provided, it is sent as-is with
                Content-Type: application/json. If a dict is provided
                without files, it is sent as form data.
            files: File attachments for multipart uploads.

        Returns:
            Parsed JSON response as a dictionary, or an empty dict if no
            content.

        Raises:
            exceptions.HTTPError: If the server returns a non-2xx status
                code (except 404).
            exceptions.NotFoundError: If the server returns HTTP 404.
            exceptions.Error: If a network-level error occurs.
        """
        url = f"{self.base_url}{endpoint}"

        # Prepare headers
        headers = dict(self.headers)

        # If data is a JSON string (not a dict), ensure correct Content-Type
        if isinstance(data, str):
            headers["Content-Type"] = constants.API_HEADER_CONTENT_TYPE_JSON

        try:
            response = self.session.request(
                method=method,
                url=url,
                headers=headers,
                params=params,
                data=data,
                files=files,
                timeout=self.timeout,
                verify=self.verify_ssl,
                allow_redirects=False,
            )
        except requests.RequestException as e:
            raise exceptions.Error(f"Network error when calling {url}: {e}") from e

        if 200 <= response.status_code < 300:
            if response.content:
                try:
                    return response.json()
                except ValueError:
                    return {}
            return {}

        if response.status_code == 404:
            raise exceptions.NotFoundError(f"Resource not found at {url}")

        message = response.text.strip() or response.reason
        raise exceptions.HTTPError(response.status_code, message, url)

    def upload_sbom(
        self,
        bom_file: str,
        auto_create: bool = False,
        project_name: str | None = None,
        project_version: str | None = None,
        project_tags: str | None = None,
        parent_name: str | None = None,
        parent_version: str | None = None,
        parent_uuid: str | None = None,
        is_latest: bool = False,
    ) -> dict:
        """Upload an SBOM file to Dependency-Track using the v5.x API.

        The SBOM (Software Bill of Materials) file is read, base64-encoded,
        and sent as a JSON payload via PUT to /api/v1/bom. The API expects
        the BOM content to be base64-encoded in the JSON request body.

        If ``auto_create`` is True, the server will create the project if it
        does not already exist. Otherwise, specify a project UUID or
        name+version.

        Args:
            bom_file: File-system path to the SBOM file to be uploaded.
            auto_create: If True, automatically create the project if needed.
            project_name: Name of the project (required if auto_create=True).
            project_version: Version of the project (required if
                auto_create=True).
            project_tags: Comma-separated tags for the project.
            parent_name: Name of a parent project, if this SBOM is nested.
            parent_version: Version of the parent project.
            parent_uuid: UUID of the parent project (overrides name/version).
            is_latest: Mark this SBOM as the latest version for the project.

        Returns:
            A dictionary containing the server's response JSON (e.g., an
            upload token).

        Raises:
            exceptions.ValidationError: If required parameters are missing or
                invalid.
            OSError: If the SBOM file cannot be opened.
            exceptions.HTTPError: If the server returns a non-2xx response.
            exceptions.Error: If a network-level error occurs.
        """
        # Input validation
        if not bom_file:
            raise exceptions.ValidationError("`bom_file` must be a non-empty path.")
        if not os.path.isfile(bom_file):
            raise exceptions.ValidationError(f"`bom_file` does not exist: {bom_file}")
        if auto_create and (not project_name or not project_version):
            raise exceptions.ValidationError(
                "`project_name` and `project_version` are required "
                "when auto_create is true."
            )

        # Read and base64-encode the SBOM file
        try:
            with open(bom_file, "rb") as f:
                bom_content = f.read()
                bom_b64 = base64.b64encode(bom_content).decode("utf-8")
        except OSError as e:
            raise OSError(f"Failed to read SBOM file `{bom_file}`: {e}") from e

        endpoint = constants.API_ENDPOINT_BOM

        # Build the JSON payload
        # Keep optional values as-is (possibly None) so the filter below can
        # drop them.
        payload: dict[str, str | None] = {
            "bom": bom_b64,
            "autoCreate": str(auto_create).lower(),
            "projectName": project_name,
            "projectVersion": project_version,
            "projectTags": project_tags,
            "parentName": parent_name,
            "parentVersion": parent_version,
            "parentUUID": parent_uuid,
            "isLatest": str(is_latest).lower(),
        }
        # Remove None values from payload
        data = {k: v for k, v in payload.items() if v is not None}

        # Convert to JSON string for the request body
        json_payload = json.dumps(data)

        return self._send_request(
            method="PUT",
            endpoint=endpoint,
            data=json_payload,
        )

    def delete_project(self, project_uuid: str) -> None:
        """Delete a project from Dependency-Track by its UUID.

        Args:
            project_uuid: UUID of the project to delete.

        Raises:
            exceptions.ValidationError: If ``project_uuid`` is not a valid UUID.
            exceptions.NotFoundError: If the project does not exist (HTTP 404).
            exceptions.HTTPError: If the server returns a non-2xx response
                (other than 404).
            exceptions.Error: If a network-level error occurs.
        """
        try:
            if not isinstance(project_uuid, str):
                raise ValueError("UUID must be a string")
            project_uuid = str(UUID(project_uuid))
        except ValueError as e:
            raise exceptions.ValidationError(
                "`project_uuid` must be a valid UUID."
            ) from e

        endpoint = f"{constants.API_ENDPOINT_PROJECT}/{project_uuid}"
        self._send_request(method="DELETE", endpoint=endpoint)

    def find_project(self, name: str, version: str) -> dict | None:
        """Find a project by name and version.

        Sends a GET to /api/v1/project with query parameters ``name`` and
        ``version``. Requires exactly one exact match in the returned array.
        Returns None if no project matches; rejects ambiguous results.

        Args:
            name: Name of the project to look up.
            version: Version of the project to look up.

        Returns:
            The unique exact matching project, or None if none found.

        Raises:
            exceptions.ValidationError: If ``name`` or ``version`` is empty.
            exceptions.HTTPError: If the server returns a non-2xx response
                (other than 404).
            exceptions.Error: If a network-level error occurs.
        """
        if not name or not version:
            raise exceptions.ValidationError(
                "Both `name` and `version` must be non-empty."
            )

        endpoint = constants.API_ENDPOINT_PROJECT
        params = {"name": name, "version": version}
        projects = self._send_request(
            method="GET",
            endpoint=endpoint,
            params=params,
        )

        if not isinstance(projects, list) or any(
            not isinstance(project, dict) for project in projects
        ):
            raise exceptions.ValidationError("Invalid project lookup response.")
        matches = [
            project for project in projects
            if project.get("name") == name and project.get("version") == version
        ]
        if len(matches) > 1:
            raise exceptions.ValidationError(
                "Ambiguous project lookup; specify an explicit project UUID."
            )
        return matches[0] if matches else None

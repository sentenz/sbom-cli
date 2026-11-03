# REST API

OWASP Dependency-Track REST API documentation.

- [1. Endpoints](#1-endpoints)
  - [1.1. Upload BOM](#11-upload-bom)
  - [1.2. Delete BOM](#12-delete-bom)
  - [1.3. Get BOM](#13-get-bom)
- [2. References](#2-references)

## 1. Endpoints

### 1.1. Upload BOM

1. API Details

    - Method: `PUT`
    - Endpoint: `/api/v1/bom`
    - Headers:
      - `X-Api-Key: your_api_key_here`
    - Request Body: JSON representation of the BOM file
    - Response: HTTP 200 OK on success, appropriate error codes on failure

2. Example Request

```bash
curl -X PUT -H "X-Api-Key: your_api_key_here" -H "Content-Type: application/json" \
     -d @sbom.json https://dependency-track.localhost/api/v1/bom
```

### 1.2. Delete BOM

1. API Details

    - Method: `DELETE`
    - Endpoint: `/api/v1/bom`
    - Headers:
      - `X-Api-Key: your_api_key_here`
    - Request Body: JSON representation of the BOM file
    - Response: HTTP 200 OK on success, appropriate error codes on failure

2. Example Request

```bash
curl -X DELETE -H "X-Api-Key: your_api_key_here" -H "Content-Type: application/json" \
     -d @sbom.json https://dependency-track.localhost/api/v1/bom
```

### 1.3. Get BOM

1. API Details

    - Method: `GET`
    - Endpoint: `/api/v1/bom`
    - Headers:
      - `X-Api-Key: your_api_key_here`
    - Response: JSON representation of the BOM file on success, appropriate error codes on failure

2. Example Request

```bash
curl -X GET -H "X-Api-Key: your_api_key_here" -H "Content-Type: application/json" \
     https://dependency-track.localhost/api/v1/bom
```

## 2. References

- Dependency-Track [REST API v1](https://dependencytrack.github.io/docs/next/reference/api/v1/) documentation.
- Dependency-Track [REST API v2](https://dependencytrack.github.io/docs/next/reference/api/v2/) documentation.

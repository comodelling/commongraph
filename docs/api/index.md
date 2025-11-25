<!--
SPDX-FileCopyrightText: 2025 CommonGraph contributors: https://github.com/comodelling/commongraph/CONTRIBUTORS.md
SPDX-License-Identifier: CC-BY-SA-4.0
-->
# API Overview

CommonGraph exposes a REST API for programmatic access to graph data.

## Quick Links

- **[Full API Documentation](http://localhost:8000/docs)** — Interactive Swagger UI (when backend is running)
- **[Endpoints Reference](endpoints.md)** — Common endpoints and examples
- **[Authentication](auth.md)** — How to authenticate with the API

## Base URL

Development: `http://localhost:8000`
Production: `https://yourdomain.com`

## Common Endpoints

### Nodes

- `GET /api/nodes` — List nodes
- `POST /api/nodes` — Create node
- `GET /api/nodes/{id}` — Get node details
- `PUT /api/nodes/{id}` — Update node
- `DELETE /api/nodes/{id}` — Delete node

### Edges

- `GET /api/edges` — List edges
- `POST /api/edges` — Create edge
- `GET /api/edges/{id}` — Get edge details
- `PUT /api/edges/{id}` — Update edge
- `DELETE /api/edges/{id}` — Delete edge

### Authentication

- `POST /api/auth/login` — Authenticate and get token
- `POST /api/auth/logout` — Invalidate token
- `GET /api/auth/me` — Get current user info

### Schemas

- `GET /api/schema` — Get platform schema
- `GET /api/schema/nodes` — List node types
- `GET /api/schema/edges` — List edge types

## Response Format

All API responses use JSON:

```json
{
  "data": { /* response data */ },
  "meta": {
    "status": "success",
    "timestamp": "2025-01-15T10:30:00Z"
  }
}
```

## Error Handling

Errors return appropriate HTTP status codes with details:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input",
    "details": [...]
  }
}
```

## Rate Limiting

API rate limits are applied per user. See [Authentication](auth.md) for details.

## Interactive Documentation

When CommonGraph is running, visit `http://localhost:8000/docs` for interactive API documentation with try-it-out functionality.

## Next Steps

- Review [Endpoints](endpoints.md) for examples
- Learn about [Authentication](auth.md)
- Check full docs at `/docs` endpoint

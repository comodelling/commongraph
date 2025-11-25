<!--
SPDX-FileCopyrightText: 2025 CommonGraph contributors: https://github.com/comodelling/commongraph/CONTRIBUTORS.md
SPDX-License-Identifier: CC-BY-SA-4.0
-->
# API Endpoints

Common API endpoints and example usage.

## Nodes

### List Nodes

```bash
GET /api/nodes
```

Optional query parameters:
- `type` — Filter by node type
- `limit` — Number of results (default: 100)
- `offset` — Pagination offset

### Get Node

```bash
GET /api/nodes/{node_id}
```

### Create Node

```bash
POST /api/nodes
Content-Type: application/json

{
  "type": "project",
  "properties": {
    "title": "My Project",
    "description": "Project description"
  }
}
```

### Update Node

```bash
PUT /api/nodes/{node_id}
Content-Type: application/json

{
  "properties": {
    "title": "Updated Title"
  }
}
```

### Delete Node

```bash
DELETE /api/nodes/{node_id}
```

## Edges

### List Edges

```bash
GET /api/edges
```

### Create Edge

```bash
POST /api/edges
Content-Type: application/json

{
  "type": "collaborates",
  "source_id": "{node_id_1}",
  "target_id": "{node_id_2}",
  "properties": {
    "description": "How they collaborate"
  }
}
```

## Authentication

### Login

```bash
POST /api/auth/login
Content-Type: application/json

{
  "username": "user",
  "password": "password"
}
```

Response includes `access_token`.

### Using Token

Include in request header:

```bash
Authorization: Bearer {access_token}
```

## Schema

### Get Schema

```bash
GET /api/schema
```

Returns complete platform schema.

### Node Types

```bash
GET /api/schema/nodes
```

### Edge Types

```bash
GET /api/schema/edges
```

## More Examples

For complete and interactive examples, visit the API documentation at:

```
http://localhost:8000/docs
```

(when backend is running)

See [Authentication](auth.md) for API access details.

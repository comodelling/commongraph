<!--
SPDX-FileCopyrightText: 2025 CommonGraph contributors: https://github.com/comodelling/commongraph/CONTRIBUTORS.md
SPDX-License-Identifier: CC-BY-SA-4.0
-->
# Data Model

The underlying data structures in CommonGraph.

## Core Entities

### Nodes

Represents an entity in the knowledge graph.

**Core Fields:**
- `id` — Unique identifier (UUID)
- `node_type` — Type (from schema)
- `properties` — Custom attributes defined in schema
- `created_at` — Creation timestamp
- `created_by` — Username who created the node
- `updated_at` — Last modification timestamp

**Predefined Properties** (optional, configurable per node type):
- `title` — Display name
- `scope` — Category or project grouping
- `status` — draft | live | realised | unrealised
- `description` — Long-form text
- `tags` — List of tags for filtering
- `references` — List of URLs or citations

### Edges

Represents a relationship between two nodes.

**Fields:**
- `id` — Unique identifier
- `type` — Edge type (from schema)
- `source_id` — ID of source node
- `target_id` — ID of target node
- `properties` — Custom attributes (defined in schema)
- `created_at` — Creation timestamp
- `created_by` — User who created the edge
- `updated_at` — Last modification timestamp

### Users

Platform users with authentication and permissions.

**Fields:**
- `id` — Unique identifier
- `username` — Login name
- `email` — Email address
- `password_hash` — Hashed password
- `role` — User role (admin, contributor, viewer)
- `is_active` — Account status
- `created_at` — Timestamp

## Permissions

Permissions define access levels for operations:

- **Read** — View nodes and edges
- **Create** — Add new nodes and edges
- **Edit** — Modify existing nodes and edges
- **Delete** — Remove nodes and edges
- **Rate** — Submit poll and rating responses

Each permission has a level:
- `all` — Everyone
- `loggedin` — Authenticated users
- `admin` — Administrators only

## Polls & Ratings

Users can provide feedback on nodes and edges:

**Poll:**
- Question with discrete options
- Multiple responses aggregated
- Linked to node or edge types

**Rating:**
- Numerical or discrete response
- Accumulated across users
- Shows community consensus

## Schema

Defines the structure of your platform:

**Node Type:**
- Name (e.g., `project`)
- Properties with types

**Edge Type:**
- Name (e.g., `collaborates`)
- Properties with types

**Poll:**
- Question text
- Answer options
- Applicable node/edge types

## Database Schema

CommonGraph stores data in PostgreSQL with normalised tables:

**Graph Data:**
- `node` — Node instances
- `edge` — Edge instances
- `graphhistoryevent` — Change log for all graph operations
- `ratingevent` — Poll and rating responses

**Users:**
- `user` — Platform users with roles
- `scope` — Scope categories (auto-created)
- `tag` — Tags for content organisation

**Schema Management:**
- `graphschema` — Schema versions with config hash
- `schemamigration` — Migration tracking between versions

**Security:**
- `securityquestion` — For password recovery

Most application logic works through the API; direct database access is not recommended.

## Data Integrity

- Referential integrity enforced at database layer
- Cascading deletes where appropriate
- Transaction support for multi-step operations
- Audit trail of changes (created_at, created_by, updated_at)

## Next Steps

- Understand the [System Overview](overview.md)
- Learn about [Configuration](../user-guide/configuration.md)
- See the [API Reference](../api/endpoints.md)

<!--
SPDX-FileCopyrightText: 2025 CommonGraph contributors: https://github.com/comodelling/commongraph/CONTRIBUTORS.md
SPDX-License-Identifier: CC-BY-SA-4.0
-->
# System Overview

High-level architecture of CommonGraph.

## Components

CommonGraph comprises three main components:

### 1. Backend (FastAPI)

- Handles REST API requests
- Manages authentication and authorisation
- Enforces business logic and permissions
- Interfaces with PostgreSQL

**Technology:** Python, FastAPI, SQLAlchemy

**Location:** `/backend`

### 2. Frontend (Vue.js)

- Web interface for end-users
- Handles graph visualisation
- Manages state and UI interactions
- Communicates with backend API

**Technology:** Vue 3, Vite

**Location:** `/frontend`

### 3. Database (PostgreSQL)

- Stores nodes, edges, users, and metadata
- Maintains schema information
- Handles transactions and data integrity

**Location:** Docker container (see Deployment)

## Data Flow

```
User → Frontend (Vue)
         ↓
       API (FastAPI)
         ↓
     Database (PostgreSQL)
```

1. User interacts with frontend interface
2. Frontend sends API request to backend
3. Backend validates permissions and business logic
4. Backend queries or updates database
5. Response sent back through API
6. Frontend updates UI with new data

## Configuration & Schema Management

Platform configuration is defined in YAML files (`config/` directory):

- Specifies node and edge types with properties
- Defines permissions and authentication
- Configures polls and rating questions
- Sets platform branding and content licensing
- Customises visual styling

Configuration is loaded at startup. CommonGraph tracks schema versions in the database:
- **Schema versioning** — Each config change creates a new schema version
- **Migration tracking** — Changes are logged with timestamps and user info
- **Schema API** — Frontend fetches current schema to render forms dynamically

## Optional Components

### JanusGraph

For large-scale graph analysis:
- Provides advanced graph queries
- Optimised for traversals and analytics
- Optional; standard deployments use PostgreSQL alone

## Security Model

- User authentication via username/password or tokens
- Role-based access control (RBAC)
- Permissions enforced at API layer
- Password hashing with bcrypt
- HTTPS/SSL in production

## Deployment

See [Deployment documentation](../deployment/index.md) for:
- Local development setup
- Production deployment
- Docker Compose services

## Next Steps

- Learn about the [Data Model](data-model.md)
- Review [Contributing](../contributing/index.md) to help develop

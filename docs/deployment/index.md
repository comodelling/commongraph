<!--
SPDX-FileCopyrightText: 2025 CommonGraph contributors: https://github.com/comodelling/commongraph/CONTRIBUTORS.md
SPDX-License-Identifier: CC-BY-SA-4.0
-->
# Deployment

This section covers running CommonGraph in development and production environments.

## Quick Navigation

- **[Development Setup](development.md)** — Local development environment
- **[Production Deployment](production.md)** — Running in production
- **[Docker Compose](docker-compose.md)** — Using compose.sh for operations

## Choose Your Path

### Development

Perfect for:
- Learning CommonGraph
- Testing configurations
- Local development work

**Start here:** [Development Setup](development.md)

### Production

For:
- Live platforms
- Multiple users
- Data persistence and backups
- SSL/TLS encryption

**Start here:** [Production Deployment](production.md)

## Common Tasks

- Starting and stopping services
- Resetting the database
- Viewing logs
- Managing SSL certificates

All covered in the relevant deployment guide.

## Overview

CommonGraph uses **Docker Compose** for easy deployment. The `compose.sh` script simplifies common operations.

Core services:

- **PostgreSQL** — Primary data store
- **Backend (FastAPI)** — REST API
- **Frontend (Vue)** — Web interface
- **Nginx** — Reverse proxy and static file server

!!! warning "JanusGraph - Under Development"
    **JanusGraph** (optional) — Graph database for large-scale deployments.

    ⚠️ **Currently under development** — The JanusGraph integration is experimental and not recommended for production use yet.

See [Docker Compose](docker-compose.md) for service details.

<!--
SPDX-FileCopyrightText: 2025 CommonGraph contributors: https://github.com/comodelling/commongraph/CONTRIBUTORS.md
SPDX-License-Identifier: CC-BY-SA-4.0
-->
# Docker Compose Reference

Understanding and managing CommonGraph services with Docker Compose.

## Services

CommonGraph uses the following services:

### PostgreSQL

Primary relational database storing nodes, edges, users, and configuration.

- **Port:** 5432
- **Environment:** POSTGRES_PASSWORD, POSTGRES_USER, POSTGRES_DB
- **Persistence:** Docker volume

### Backend (FastAPI)

REST API providing graph operations, authentication, and business logic.

- **Port:** 8000
- **Language:** Python
- **Docs:** http://localhost:8000/docs

### Frontend (Vue.js)

Web interface for viewing and interacting with the graph.

- **Port:** 5173 (dev) / via Nginx (prod)
- **Technology:** Vue 3, Vite
- **Builds to:** Static assets

### Nginx

Reverse proxy, SSL termination, and static file serving.

- **Port:** 80, 443 (production)
- **Config:** Templates in `nginx/`

### JanusGraph (Optional)

Large-scale graph processing and analytics.

- **Port:** 8182
- **Enable:** Set `ENABLE_GRAPH_DB=true` in `.env`

## Using compose.sh

The `compose.sh` script wraps Docker Compose with convenience commands:

```bash
./compose.sh up                 # Start services
./compose.sh down               # Stop services
./compose.sh logs [service]     # View logs
./compose.sh shell [service]    # Open container shell
./compose.sh reset-db           # Reset database
./compose.sh setup-ssl          # Bootstrap SSL (production)
```

## Docker Compose Files

- `docker-compose.yaml` — Core services
- `docker-compose.dev.yaml` — Development overrides
- `docker-compose.prod.yaml` — Production overrides
- `docker-compose.janusgraph.yaml` — Graph database (optional)

## Environment Variables

Key variables in `.env`:

| Variable | Purpose | Example |
|----------|---------|---------|
| `APP_ENV` | development or production | development |
| `CONFIG_FILE` | Platform configuration file | config/config-example.yaml |
| `DOMAIN` | Domain name | localhost |
| `POSTGRES_PASSWORD` | Database password | your_password |
| `BACKEND_PORT` | Backend API port | 8000 |
| `FRONTEND_PORT` | Frontend port | 5173 |
| `ENABLE_GRAPH_DB` | Enable JanusGraph | false |

## Viewing Logs

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f backend

# Last 100 lines
docker compose logs --tail=100 backend
```

## Shell Access

Open a shell inside a running container:

```bash
./compose.sh shell backend
./compose.sh shell postgres
```

## Stopping & Starting

```bash
# Stop containers (preserves data)
./compose.sh down

# Stop and remove volumes (deletes data)
./compose.sh down -v

# Start services again
./compose.sh up
```

## Common Issues

**Port already in use?**
Change `BACKEND_PORT` or `FRONTEND_PORT` in `.env`.

**Database won't connect?**
Ensure PostgreSQL is running: `docker compose ps postgres`

**Containers keep restarting?**
Check logs: `docker compose logs backend`

More troubleshooting coming soon.

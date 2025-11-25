<!--
SPDX-FileCopyrightText: 2025 CommonGraph contributors: https://github.com/comodelling/commongraph/CONTRIBUTORS.md
SPDX-License-Identifier: CC-BY-SA-4.0
-->
# Development Setup

Set up CommonGraph for local development work.

## Prerequisites

- Docker and Docker Compose
- Git
- Text editor
- Python 3.13+ (optional, for running backend outside containers)
- Node.js 18+ (optional, for running frontend outside containers)

## Local Setup with Docker

### 1. Clone Repository

```bash
git clone https://github.com/comodelling/commongraph.git
cd commongraph
```

### 2. Create Environment File

```bash
cp .env.example .env
```

Set `APP_ENV=development` in your `.env`.

### 3. Start Services

```bash
./compose.sh up
```

### 4. Access Services

- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs
- PostgreSQL: localhost:5432

## Running Services Locally

For faster development iteration, you can run services outside containers.

### Backend

```bash
cd backend
pip install -r requirements-dev.txt
uvicorn main:app --reload
```

Backend will start on http://localhost:8000.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend will start on http://localhost:5173.

PostgreSQL can still run in Docker:

```bash
docker run -e POSTGRES_PASSWORD=password -p 5432:5432 postgres:15
```

## Database

### Reset Database

```bash
./compose.sh reset-db
```

This will:
- Stop all services
- Remove database volume
- Reinitialise databases
- Restart services

### View Logs

```bash
./compose.sh logs [service_name]
```

Examples:
```bash
./compose.sh logs backend
./compose.sh logs frontend
./compose.sh logs postgres
```

## Workflow

1. Make code changes
2. If running in containers: restart services with `./compose.sh down && ./compose.sh up`
3. If running locally: changes auto-reload with Uvicorn/Vite
4. Test at http://localhost:5173
5. Check API docs at http://localhost:8000/docs

## Testing

### Backend Tests

```bash
cd backend
pytest
```

### Frontend Tests

```bash
cd frontend
npm run test
```

## Troubleshooting

**Port already in use?**
```bash
# Change in .env
BACKEND_PORT=8001
FRONTEND_PORT=5174
```

**Database connection failed?**
```bash
./compose.sh reset-db
```

**Container won't start?**
```bash
docker compose logs backend  # See what went wrong
```

## Next Steps

- Read [Basic Concepts](../getting-started/concepts.md)
- Review [Configuration](../user-guide/configuration.md)
- Check out [Contributing](../contributing/index.md) guidelines

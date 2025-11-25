<!--
SPDX-FileCopyrightText: 2025 CommonGraph contributors: https://github.com/comodelling/commongraph/CONTRIBUTORS.md
SPDX-License-Identifier: CC-BY-SA-4.0
-->
# Quick Start

Get CommonGraph running on your machine in about 10 minutes.

## Prerequisites

- Docker and Docker Compose installed
- Git
- A text editor

## Setup

### 1. Clone and Navigate

```bash
git clone https://github.com/comodelling/commongraph.git
cd commongraph
```

### 2. Configure Environment

Copy the example environment file and customise it:

```bash
cp .env.example .env
```

Open `.env` and update the following (for development):

```env
CONFIG_FILE=config/config-example.yaml
APP_ENV=development
DOMAIN=localhost
POSTGRES_PASSWORD=your_password
INITIAL_ADMIN_PASSWORD=your_password
```

### 3. Start Services

```bash
./compose.sh up
```

The script will:
- Start PostgreSQL and initialise databases
- Launch the backend API (http://localhost:8000)
- Start the frontend (http://localhost:5173)
- Create an admin user with your credentials

### 4. Access CommonGraph

- **Frontend:** http://localhost:5173
- **API Docs:** http://localhost:8000/docs
- **Login:** Use the credentials from your `.env` file

## Next Steps

- Read [Basic Concepts](concepts.md) to understand nodes and edges
- Explore the [Platform Setup](../user-guide/setup.md) guide
- Review [Configuration](../user-guide/configuration.md) options

## Troubleshooting

**Containers won't start?**
- Check Docker is running: `docker ps`
- Review logs: `./compose.sh logs backend`

**Database connection errors?**
- Ensure `.env` is properly configured
- Run: `./compose.sh reset-db` to reset

**Port conflicts?**
- Change `BACKEND_PORT` and `FRONTEND_PORT` in `.env`

For more detailed troubleshooting, see [Deployment](../deployment/index.md).

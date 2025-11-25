<!--
SPDX-FileCopyrightText: 2025 CommonGraph contributors: https://github.com/comodelling/commongraph/CONTRIBUTORS.md
SPDX-License-Identifier: CC-BY-SA-4.0
-->
# Production Deployment

Running CommonGraph in production for your community.

## Prerequisites

- A server or cloud instance (VPS, dedicated server, or cloud provider)
- Docker and Docker Compose installed
- A domain name with DNS configured to point to your server
- SSL certificate (automatically obtained via Let's Encrypt)
- Strong passwords for admin account and database

CommonGraph is free and open source—you're in full control of your deployment and data.

## Environment Configuration

Create `.env` and `.env.production` files:

**.env**
```env
CONFIG_FILE=config/config-myplatform.yaml
APP_ENV=production
DOMAIN=yourdomain.com
BACKEND_PORT=8000
FRONTEND_PORT=5173

POSTGRES_PASSWORD=your_very_strong_password
INITIAL_ADMIN_PASSWORD=your_very_strong_admin_password
```

**.env.production** (optional overrides)
```env
# Add any production-specific settings here
```

## SSL Certificate Setup

CommonGraph includes automated SSL setup via Let's Encrypt:

```bash
./compose.sh setup-ssl
```

This will:
- Validate your domain
- Obtain SSL certificates from Let's Encrypt
- Configure Nginx with HTTPS
- Auto-renew certificates in the background

Requirements:
- Domain must be publicly accessible
- Port 80 must be reachable
- Certificate will be auto-renewed

## Deployment

### Initial Deploy

```bash
./compose.sh up
```

Services will start with:
- PostgreSQL for data storage
- Backend API with FastAPI
- Frontend with Vue.js
- Nginx reverse proxy with SSL
- Automatic database initialisation

### Monitoring

View service status:
```bash
docker compose ps
```

Check logs:
```bash
./compose.sh logs [service_name]
```

### Database Backups

!!! warning
    Implement regular database backups before going live.

PostgreSQL can be backed up with:
```bash
docker compose exec postgres pg_dump -U postgres commongraph_db > backup.sql
```

## Optional: JanusGraph

For very large graphs, enable the optional graph database:

In `.env`:
```env
ENABLE_GRAPH_DB=true
```

Then start:
```bash
./compose.sh up
```

## Best Practices

- Use strong, unique passwords
- Enable automatic backups
- Monitor disk space and database size
- Keep dependencies updated
- Review logs regularly
- Set up log aggregation for debugging

## Scaling Considerations

For high-traffic deployments:
- Use a managed PostgreSQL service
- Run multiple backend instances behind load balancer
- Use CDN for frontend assets
- Consider JanusGraph for graph-heavy queries
- Monitor performance and optimise as needed

## Support

For production issues, check the [Troubleshooting](../contributing/index.md) section (coming soon) or contact support.

<!--
SPDX-FileCopyrightText: 2025 CommonGraph contributors: https://github.com/comodelling/commongraph/CONTRIBUTORS.md
SPDX-License-Identifier: CC-BY-SA-4.0
-->
# Authentication

How to authenticate with the CommonGraph API.

## Bearer Token Authentication

CommonGraph uses JWT-based bearer tokens for API authentication.

### Obtaining a Token

1. **Login via API:**

```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "your_username",
    "password": "your_password"
  }'
```

Response:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

### Using the Token

Include the token in the `Authorization` header:

```bash
curl http://localhost:8000/api/nodes \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

## Web Interface

Users logging into the web interface (http://localhost:5173) are automatically authenticated. Tokens are stored securely and managed by the frontend.

## Token Expiration

Tokens expire after a period (default: 1 hour). When expired, login again to obtain a new token.

## Permissions

API endpoints respect the same permission model as the web interface:

- `read` permissions allow GET requests
- `create` permissions allow POST requests
- `edit` permissions allow PUT requests
- `delete` permissions allow DELETE requests

If you lack the required permission, the API returns a 403 Forbidden response.

## Rate Limiting

API requests are rate-limited per user:
- Default: 1000 requests per hour
- Exceeding the limit returns a 429 Too Many Requests response

## Best Practices

- Store tokens securely (not in version control or client-side code)
- Use HTTPS in production to prevent token interception
- Rotate tokens regularly
- Use short-lived tokens for scripts
- Consider API keys for service-to-service communication (coming soon)

## Troubleshooting

**"Invalid credentials" error?**
Verify username and password are correct.

**"Token expired" error?**
Obtain a new token by logging in again.

**"Permission denied" error?**
Check your user permissions in the admin panel.

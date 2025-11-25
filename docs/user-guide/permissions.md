<!--
SPDX-FileCopyrightText: 2025 CommonGraph contributors: https://github.com/comodelling/commongraph/CONTRIBUTORS.md
SPDX-License-Identifier: CC-BY-SA-4.0
-->
# Users & Permissions

Managing users and access control in CommonGraph.

## User Roles

CommonGraph has a three-tier role system:

### Regular Users
- Default role for all users
- Interact with content according to platform permissions
- Cannot manage other users

### Admins
- Approve new user signups
- Promote/demote regular users to/from admin
- Edit protected content (change node/edge types, titles, scopes)
- Cannot demote super admins

### Super Admins
- Highest privilege level
- Can manage admin status for all users including other super admins
- Cannot be demoted by regular admins
- Typically reserved for platform founders and key stakeholders

See [user-roles.md](https://github.com/comodelling/commongraph/blob/dev/docs/user-roles.md) for the complete role hierarchy.

## Permission Model

Permissions are configured at the platform level for:

- **Read** — Who can view content
- **Create** — Who can add new nodes and edges
- **Edit** — Who can modify existing content
- **Delete** — Who can remove content
- **Rate** — Who can respond to polls and ratings

Each permission can be set to:
- `all` — Everyone, including unauthenticated users
- `loggedin` — Authenticated users only
- `admin` — Administrators only

## Authentication

CommonGraph supports:
- **Username/password** authentication
- **Admin approval workflow** for new signups
- **Access tokens** for API access

Configuration is managed in your platform's `auth` settings.

## Managing Users

!!! warning
    User management UI is being developed. For now, use the database directly or contact your administrator.

## Best Practices

- Start restrictive (e.g., `loggedin` for create)
- Broaden permissions gradually as needed
- Regularly review user access
- Use the `admin` role for sensitive operations
- Enable signup approval for communities

More user management tools coming in future versions.

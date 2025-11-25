<!--
SPDX-FileCopyrightText: 2025 CommonGraph contributors: https://github.com/comodelling/commongraph/CONTRIBUTORS.md
SPDX-License-Identifier: CC-BY-SA-4.0
-->
# Platform Setup

This guide walks you through configuring a CommonGraph platform for your community.

## Configuration Basics

CommonGraph platforms are configured via YAML files in the `config/` directory. Each configuration defines:
- Platform name, tagline and description
- Node and edge types with their properties
- Polls and rating questions
- Visual styling (colours, shapes)
- Authentication and signup settings
- Permission levels
- Content licensing

## Creating Your First Platform

### 1. Create a Configuration File

Copy an existing config as a starting point:

```bash
cp config/config-example.yaml config/config-myplatform.yaml
```

### 2. Update Your Environment

Update `.env` to point to your new config:

```env
CONFIG_FILE=config/config-myplatform.yaml
```

### 3. Customise Your Platform

Edit `config-myplatform.yaml` with your platform details (see [Configuration Reference](configuration.md)).

### 4. Restart and Verify

```bash
./compose.sh down
./compose.sh up
```

Visit http://localhost:5173 to see your platform live.

## Configuration Structure

A basic configuration includes:

```yaml
platform_name: My Platform
platform_tagline: A collaborative knowledge network
platform_description: HTML-formatted description here

node_types:
  project:
    properties:
      - title
      - description
      - status

edge_types:
  collaborates:
    properties:
      - description
      - start_date

polls:
  alignment:
    type: discrete
    question: Is this aligned with our goals?
    options:
      - 1: "Very aligned"
      - 2: "Somewhat aligned"
      - 3: "Not aligned"
    node_types: ["project"]

auth:
  allow_signup: true
  signup_requires_admin_approval: true

permissions:
  read: loggedin
  create: loggedin
  edit: all
  delete: admin

license: "CC BY-SA"
```

## Next Steps

- Review the full [Configuration Reference](configuration.md)
- Learn how to [manage content](content.md)
- Set up [users and permissions](permissions.md)
- Deploy to production (see [Deployment](../deployment/index.md))

## Need Help?

Stuck on configuration? Check the `config/` directory for examples, or open an issue on GitHub.

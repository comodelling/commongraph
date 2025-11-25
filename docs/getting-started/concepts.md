<!--
SPDX-FileCopyrightText: 2025 CommonGraph contributors: https://github.com/comodelling/commongraph/CONTRIBUTORS.md
SPDX-License-Identifier: CC-BY-SA-4.0
-->
# Basic Concepts

CommonGraph is built around a few core ideas. Understanding these will help you get the most from the platform.

## Nodes

Nodes are entities in your knowledge graph. Think of them as the "things" that matter to your community—people, projects, ideas, organisations, outcomes, tools, objectives, or anything else.

Each node has:

- A **type** (defined in your schema)
- **Properties** (custom fields you configure)
- A **creation timestamp** and **creator**
- Optional **ratings** and **polls**

### Pre-defined Properties

These optional properties are available for any node type:

- **title** — Display name
- **scope** — Optional categorisation for grouping related content
- **status** — Optional: draft, live, realised, unrealised
- **description** — Long-form text
- **tags** — List of tags for filtering
- **references** — List of URLs or citations

You choose which pre-defined properties to enable for each node type in your schema.

### Custom Properties

Define your own properties with different types:

- **Discrete options** — Multiple choice with custom question and options
- **Continuous ranges** — Numeric values within a specified range
- **Text fields** — Free-form text

Example node types:

- `project` with properties: title, description, status
- `objective` with properties: title, description, references
- `tool` with a custom property for "maturity level" (discrete options: alpha, beta, stable)

## Edges

Edges represent relationships between nodes. They're how you build the graph—connecting nodes to show how things relate.

Like nodes, edges have:

- A **type** (defined in configuration)
- **Properties** (contextual information about the relationship)
- A **source node** and **target node**
- Optional **ratings** and **polls**

Edges can also use pre-defined properties (description, references, tags) and custom properties (discrete or continuous).

Example edge types:

- `leads` (person → project)
- `influences` (outcome → outcome)
- `contributes_to` (person → project) with a custom "role" property

## Schemas

A schema defines the structure of your platform. It specifies:

- Available **node types** and their properties
- Available **edge types** and their properties
- **Polls** (questions you can ask about nodes or edges)
- **Property types** (pre-defined like title/scope/status, or custom with discrete options or continuous ranges)
- **Visual styling** for each type (colours, border radius)

Schemas are defined in YAML configuration files. CommonGraph tracks schema versions and migrations, allowing you to evolve your data model over time.

## Scopes

Scopes let you organise nodes into categories or projects. They're like tags but with special functionality:

- Filter nodes by scope in the interface
- Auto-create scopes when referenced
- Use scopes to organise work streams or thematic areas

Scopes are completely optional but helpful for larger platforms with multiple focus areas.

## Permissions

CommonGraph supports flexible permission levels for each operation:

- **Read** — View and search nodes and edges
- **Create** — Add new nodes and edges
- **Edit** — Modify existing content
- **Delete** — Remove content
- **Rate** — Submit ratings on polls

Each permission can be configured as:

- `all` — Anyone, including anonymous users
- `loggedin` — Authenticated users only
- `admin` — Administrators and super admins only

### User Roles

Three user roles with different privileges:

- **Regular Users** — Interact with content according to platform permissions
- **Admins** — Manage users, approve signups, moderate content
- **Super Admins** — Permanent administrators who can manage other admins

### Content Status & Edit Protection

Nodes and edges can have optional status levels that affect editing:

- **draft** — Anyone with edit permissions can modify all fields
- **live/realised/unrealised** — Only admins can change type, title, scope, or revert to draft. Regular users can still edit description, references, and tags.

## Polls & Ratings

Gather collective feedback on any node or edge:

- **Polls** ask specific questions with discrete or continuous response options
- **Ratings** aggregate individual responses to show community consensus
- Configure different polls for different node or edge types
- Results help communities make informed, collective assessments

## Let's Get Practical

Ready to see this in action? Check the [Platform Setup](../user-guide/setup.md) guide to configure your first platform, or review the [Configuration](../user-guide/configuration.md) reference for detailed options.

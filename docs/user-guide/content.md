<!--
SPDX-FileCopyrightText: 2025 CommonGraph contributors: https://github.com/comodelling/commongraph/CONTRIBUTORS.md
SPDX-License-Identifier: CC-BY-SA-4.0
-->
# Managing Content

How to work with nodes, edges, and data in CommonGraph.

## Creating Nodes

Through the frontend interface, users with `create` permissions can add new nodes:

1. Navigate to the main graph view
2. Click **Create Node**
3. Select a node type
4. Fill in properties
5. Save

## Creating Edges

To connect nodes:

1. Select a source node
2. Click **Create Connection** (or similar UI element)
3. Choose an edge type
4. Select the target node
5. Add any edge properties
6. Save

## Editing Content

Users with `edit` permissions can modify nodes and edges. The platform tracks edit history and maintains version information.

## Deleting Content

Only users with `delete` permissions can remove nodes or edges.

## Exploring the Graph

Users can explore the knowledge graph through:

- **Graph visualisation** — Interactive network view with zoom and pan
- **Search** — Find nodes by type, title, or scope
- **Filtering** — Show/hide node and edge types
- **Element focus** — Click any node or edge to see details and connections

## Exporting Data

### Full Graph Export

Export the entire graph as JSON:

```bash
GET /api/graph/export
```

Returns all nodes, edges, and their properties.

### Subgraph Export

From the graph/flow view interface, you can also export a **subgraph** — just the visible nodes and edges currently displayed. This is useful for:

- Sharing a specific subset of your graph
- Analysing a particular area of interest
- Creating focused datasets

Both exports use JSON format, useful for:

- Backing up your data
- Analysing the graph externally
- Migrating between platforms
- Sharing datasets

## Importing Data

Import structured data from JSON files matching the export format. See `data/` directory for examples.

More import documentation coming soon.

## Polls & Ratings

### Submitting a Rating

1. Navigate to a node or edge
2. Find the poll/rating section
3. Select your response
4. Submit

### Viewing Results

Aggregate results show community consensus and are updated in real-time.

## Best Practices

- Define your schema before bulk importing data
- Use consistent naming for properties
- Test permissions before going live
- Keep descriptions clear and helpful
- Archive rather than delete when possible

More guidance coming soon.

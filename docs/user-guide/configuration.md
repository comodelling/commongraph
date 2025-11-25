<!--
SPDX-FileCopyrightText: 2025 CommonGraph contributors: https://github.com/comodelling/commongraph/CONTRIBUTORS.md
SPDX-License-Identifier: CC-BY-SA-4.0
-->
# Configuration Reference

Complete reference for CommonGraph platform configuration files.

## Structure

CommonGraph platforms are configured via YAML files with the following sections:

### Platform Metadata

```yaml
platform_name: Your Platform Name
platform_tagline: A short tagline
platform_description: A longer description supporting HTML
```

### Node Types

Define the types of entities in your graph:

```yaml
node_types:
  node_type_name:
    properties:
      # Pre-defined properties (optional):
      - title
      - scope
      - status
      - description
      - tags
      - references
      # Custom properties with discrete options:
      - maturity:
          type: discrete
          question: What's the maturity level?
          options:
            - alpha: Alpha
            - beta: Beta
            - stable: Stable
```

**Pre-defined properties** are built-in and have special UI handling. You only include the ones you want for each node type.

**Custom properties** let you define domain-specific fields with discrete choices or continuous ranges.

### Edge Types

Define the types of relationships:

```yaml
edge_types:
  edge_type_name:
    properties:
      - property_name
      - custom_property:
          type: discrete
          question: Display question for this property
          options:
            - value_1: Label 1
            - value_2: Label 2
    style:
      color: "#ff6b6b"
      width: 2
```

### Visual Styling

Customise appearance for each node and edge type:

```yaml
node_types:
  my_node:
    style:
      borderColor: "#23cdff"
      borderRadius: "50px"  # Circular nodes
      # Or use "15px" for rounded corners, "3px" for sharp edges
```

### Polls

Define surveys or questions:

```yaml
polls:
  poll_name:
    type: discrete
    question: The question to ask?
    options:
      - 1: "Option 1"
      - 2: "Option 2"
    node_types: ["applicable_node_type"]
    edge_types: []
```

### Authentication

```yaml
auth:
  allow_signup: true
  signup_requires_admin_approval: true
  signup_requires_token: false
```

### Permissions

Control access levels:

```yaml
permissions:
  read: loggedin      # all | loggedin | admin
  create: loggedin
  edit: all
  delete: admin
  rate: all
```

### Licensing

Specify content licence:

```yaml
license: "CC BY-SA"  # Supported: CC BY, CC BY-SA, CC BY-NC, etc., CC0, CC PDM
```

## Examples

See the `config/` directory in the repository for complete working examples.

## Tips

- Keep property names lowercase and use underscores
- Test configuration changes locally before deploying
- Permissions follow a pattern: `all` > `loggedin` > `admin`
- Reload the platform to apply configuration changes

More detailed documentation coming soon.

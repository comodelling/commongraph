import yaml
from pathlib import Path

# 1. Locate & load your YAML
_CONFIG_PATH = Path(__file__).parent.parent / "config.yaml"
_CONFIG = yaml.safe_load(_CONFIG_PATH.read_text())

PLATFORM_NAME = _CONFIG.get("platform_name", "CommonGraph")
NODE_TYPE_CFG  = _CONFIG["node_types"]
EDGE_TYPE_CFG  = _CONFIG["edge_types"]
POLLS_CFG  = _CONFIG["polls"]

# 2. Build maps for properties
NODE_TYPE_PROPS = {
    nt: set(defn.get("properties", []))
    for nt, defn in NODE_TYPE_CFG.items()
}
EDGE_TYPE_PROPS = {
    et: set(defn.get("properties", []))
    for et, defn in EDGE_TYPE_CFG.items()
}

# 3. Build maps for styles
NODE_TYPE_STYLE = {
    nt: defn.get("style", {})
    for nt, defn in NODE_TYPE_CFG.items()
}
EDGE_TYPE_STYLE = {
    et: defn.get("style", {})
    for et, defn in EDGE_TYPE_CFG.items()
}

#. 4
EDGE_TYPE_BETWEEN = {
    et: defn.get("between", None)
    for et, defn in EDGE_TYPE_CFG.items()
}

# .5 Polls configuration

def get_node_type_polls() -> dict:
    """Return the polls configuration per node or edge type."""
    out = {k: {} for k in NODE_TYPE_CFG}
    for k, v in POLLS_CFG.items():
        for tp in v['node_types']:
            out[tp][k] = v
    return out

def get_edge_type_polls() -> dict:
    """Return the polls configuration per edge type."""
    out = {k: {} for k in EDGE_TYPE_CFG}
    for k, v in POLLS_CFG.items():
        for tp in v['edge_types']:
            out[tp][k] = v
    return out

NODE_TYPE_POLLS = get_node_type_polls()
EDGE_TYPE_POLLS = get_edge_type_polls()


# 5. Helpers
def valid_node_types() -> set[str]:
    return set(NODE_TYPE_PROPS)

def valid_edge_types() -> set[str]:
    return set(EDGE_TYPE_PROPS)

def filter_node_props(node_type: str, data: dict) -> dict:
    allowed = NODE_TYPE_PROPS.get(node_type, set())
    return {k: v for k, v in data.items() if k in allowed}

def filter_edge_props(edge_type: str, data: dict) -> dict:
    allowed = EDGE_TYPE_PROPS.get(edge_type, set())
    return {k: v for k, v in data.items() if k in allowed}
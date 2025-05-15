import yaml
from pathlib import Path

# 1. Locate & load your YAML
_CONFIG_PATH = Path(__file__).parent.parent / "config.yaml"
_CONFIG = yaml.safe_load(_CONFIG_PATH.read_text())

METAMODEL      = _CONFIG["metamodel"]
NODE_TYPE_CFG  = METAMODEL["node_types"]
EDGE_TYPE_CFG  = METAMODEL["edge_types"]

# 2. Build maps: node_type -> set(properties), same for edges
NODE_TYPE_PROPS = {
    nt: set(defn.get("properties", []))
    for nt, defn in NODE_TYPE_CFG.items()
}
EDGE_TYPE_PROPS = {
    et: set(defn.get("properties", []))
    for et, defn in EDGE_TYPE_CFG.items()
}

# 3. Helpers
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
import yaml
import hashlib
import json
from pathlib import Path
from typing import Dict, Any, List, Tuple

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

# 4. between specifics for graph schema
EDGE_TYPE_BETWEEN = {
    et: defn.get("between", None)
    for et, defn in EDGE_TYPE_CFG.items()
}

# 5. Polls configuration

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

# 6. Authentication configuration
AUTH_CFG = _CONFIG.get("auth", {})
ALLOW_SIGNUP = AUTH_CFG.get("allow_signup", True)
REQUIRE_ADMIN_APPROVAL = AUTH_CFG.get("require_admin_approval", False)

# Schema versioning configuration
def _compute_config_hash(config: Dict[str, Any]) -> str:
    """Compute hash of the configuration for change detection"""
    config_str = json.dumps(config, sort_keys=True)
    return hashlib.sha256(config_str.encode()).hexdigest()

def _get_config_version() -> str:
    """Extract version from config or generate one"""
    return _CONFIG.get("config_version", "1.0.0")

CONFIG_HASH = _compute_config_hash(_CONFIG)
CONFIG_VERSION = _get_config_version()


class SchemaChangeDetector:
    """Detect and validate schema changes"""
    
    @staticmethod
    def detect_changes(old_config: Dict, new_config: Dict) -> List[Dict[str, Any]]:
        """Detect changes between two configurations"""
        changes = []
        
        # Check node type changes
        old_nodes = set(old_config.get("node_types", {}).keys())
        new_nodes = set(new_config.get("node_types", {}).keys())
        
        for added in new_nodes - old_nodes:
            changes.append({
                "type": "add_node_type",
                "node_type": added,
                "properties": new_config["node_types"][added].get("properties", [])
            })
        
        for removed in old_nodes - new_nodes:
            changes.append({
                "type": "remove_node_type",
                "node_type": removed,
                "warning": "This will affect existing nodes of this type"
            })
        
        # Check property changes for existing node types
        for node_type in old_nodes & new_nodes:
            old_props = set(old_config["node_types"][node_type].get("properties", []))
            new_props = set(new_config["node_types"][node_type].get("properties", []))
            
            for added_prop in new_props - old_props:
                changes.append({
                    "type": "add_node_property",
                    "node_type": node_type,
                    "property": added_prop
                })
            
            for removed_prop in old_props - new_props:
                changes.append({
                    "type": "remove_node_property",
                    "node_type": node_type,
                    "property": removed_prop,
                    "warning": "This will affect existing node data"
                })
        
        # Check edge type changes
        old_edges = set(old_config.get("edge_types", {}).keys())
        new_edges = set(new_config.get("edge_types", {}).keys())
        
        for added in new_edges - old_edges:
            changes.append({
                "type": "add_edge_type",
                "edge_type": added,
                "properties": new_config["edge_types"][added].get("properties", [])
            })
        
        for removed in old_edges - new_edges:
            changes.append({
                "type": "remove_edge_type",
                "edge_type": removed,
                "warning": "This will affect existing edges of this type"
            })
        
        # Check property changes for existing edge types
        for edge_type in old_edges & new_edges:
            old_props = set(old_config["edge_types"][edge_type].get("properties", []))
            new_props = set(new_config["edge_types"][edge_type].get("properties", []))
            
            for added_prop in new_props - old_props:
                changes.append({
                    "type": "add_edge_property",
                    "edge_type": edge_type,
                    "property": added_prop
                })
            
            for removed_prop in old_props - new_props:
                changes.append({
                    "type": "remove_edge_property",
                    "edge_type": edge_type,
                    "property": removed_prop,
                    "warning": "This will affect existing edge data"
                })
        
        # Check poll changes
        old_polls = set(old_config.get("polls", {}).keys())
        new_polls = set(new_config.get("polls", {}).keys())
        
        for added in new_polls - old_polls:
            changes.append({
                "type": "add_poll",
                "poll": added
            })
        
        for removed in old_polls - new_polls:
            changes.append({
                "type": "remove_poll",
                "poll": removed,
                "warning": "This will affect existing ratings"
            })
        
        return changes
    
    @staticmethod
    def validate_against_existing_data(changes: List[Dict], session) -> List[str]:
        """Validate changes against existing database data"""
        warnings = []
        
        for change in changes:
            if change["type"] == "remove_node_type":
                # Check if nodes of this type exist
                from sqlmodel import text
                result = session.exec(text(
                    "SELECT COUNT(*) FROM graphhistoryevent WHERE entity_type = 'node' AND payload->>'node_type' = :node_type AND state != 'deleted'"
                ), {"node_type": change["node_type"]}).first()
                if result and result[0] > 0:
                    warnings.append(f"Removing node type '{change['node_type']}' will affect {result[0]} existing nodes")
            
            elif change["type"] == "remove_edge_type":
                # Check if edges of this type exist
                from sqlmodel import text
                result = session.exec(text(
                    "SELECT COUNT(*) FROM graphhistoryevent WHERE entity_type = 'edge' AND payload->>'edge_type' = :edge_type AND state != 'deleted'"
                ), {"edge_type": change["edge_type"]}).first()
                if result and result[0] > 0:
                    warnings.append(f"Removing edge type '{change['edge_type']}' will affect {result[0]} existing edges")
            
            elif change["type"] == "remove_node_property":
                warnings.append(f"Removing property '{change['property']}' from '{change['node_type']}' will lose data")
            
            elif change["type"] == "remove_edge_property":
                warnings.append(f"Removing property '{change['property']}' from '{change['edge_type']}' will lose data")
        
        return warnings

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
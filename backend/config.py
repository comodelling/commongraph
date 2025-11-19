import yaml
import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List, Tuple
from enum import Enum

# load env variable CONFIG_FILE
from dotenv import load_dotenv

load_dotenv()
# Load environment variables from .env file
import os

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    FieldValidationInfo,
    ValidationError,
    field_validator,
    root_validator,
)

_BACKEND_DIR = Path(__file__).parent
_PROJECT_ROOT = (
    _BACKEND_DIR.parent if (_BACKEND_DIR.parent / "config").exists() else _BACKEND_DIR
)

# Get config file path from env, defaulting to config-test.yaml for tests or config-example.yaml
_CONFIG_FILE = os.getenv("CONFIG_FILE") or "config/config-test.yaml"
_CONFIG_PATH = _PROJECT_ROOT / _CONFIG_FILE


class ConfigError(RuntimeError):
    """Raised when the configuration file cannot be loaded or validated."""


ALLOWED_PERMISSION_LEVELS = {"all", "loggedin", "admin"}


class NodeTypeConfig(BaseModel):
    properties: List[str] = Field(default_factory=list)
    style: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(extra="allow")


class EdgeTypeConfig(BaseModel):
    properties: List[str] = Field(default_factory=list)
    style: Dict[str, Any] = Field(default_factory=dict)
    between: List[Tuple[str, str]] = Field(default_factory=list)

    model_config = ConfigDict(extra="allow")

    @field_validator("between", mode="before")
    def normalise_between(cls, value):
        if value is None:
            return []
        normalised: List[Tuple[str, str]] = []
        for entry in value:
            if isinstance(entry, dict):
                entry = tuple(entry.values())
            if not isinstance(entry, (list, tuple)) or len(entry) != 2:
                raise ValueError(
                    "Each 'between' entry must be a two-element sequence of node type names"
                )
            normalised.append((str(entry[0]), str(entry[1])))
        return normalised


class AggregationMethod(str, Enum):
    MEAN = "mean"
    MEDIAN = "median"
    COUNT = "count"


class PollConfig(BaseModel):
    question: str | None = None
    scale: str | None = None
    type: str | None = None
    options: Dict[str, str] = Field(default_factory=dict)
    range: tuple[float, float] | None = None
    node_types: List[str] = Field(default_factory=list)
    edge_types: List[str] = Field(default_factory=list)
    aggregation: AggregationMethod | None = AggregationMethod.MEDIAN

    model_config = ConfigDict(extra="allow")

    @field_validator("options", mode="before")
    def normalise_options(cls, value):
        if value is None:
            return {}
        if isinstance(value, dict):
            return {str(k): str(v) for k, v in value.items()}
        if isinstance(value, list):
            flattened: Dict[str, str] = {}
            for entry in value:
                if not isinstance(entry, dict) or len(entry) != 1:
                    raise ValueError("Each option entry must be a single-key mapping")
                key, option_value = next(iter(entry.items()))
                flattened[str(key)] = str(option_value)
            return flattened
        raise TypeError(
            "Poll options must be a mapping or a list of single-entry mappings"
        )

    @field_validator("range", mode="before")
    def normalise_range(cls, value):
        if value is None:
            return None
        if not isinstance(value, (list, tuple)) or len(value) != 2:
            raise TypeError("Poll range must be a two-element sequence")
        try:
            low = float(value[0])
            high = float(value[1])
        except (TypeError, ValueError):
            raise ValueError("Poll range values must be numeric")
        if low >= high:
            raise ValueError("Poll range must have low < high")
        return (low, high)

    @field_validator("node_types", "edge_types", mode="before")
    def normalise_type_list(cls, value):
        if value is None:
            return []
        if isinstance(value, (list, tuple)):
            return [str(item) for item in value]
        raise TypeError("Poll node_types and edge_types must be sequences")


class AuthConfig(BaseModel):
    allow_signup: bool = True
    signup_requires_admin_approval: bool = False
    signup_requires_token: bool = False

    model_config = ConfigDict(extra="allow")


class PermissionsConfig(BaseModel):
    read: str = "all"
    create: str = "all"
    edit: str = "all"
    delete: str = "all"
    rate: str = "all"

    model_config = ConfigDict(extra="allow")

    @field_validator("read", "create", "edit", "delete", "rate")
    def validate_levels(cls, value: str):
        if not isinstance(value, str):
            raise TypeError("Permission level must be a string")
        normalised = value.strip().lower()
        if normalised not in ALLOWED_PERMISSION_LEVELS:
            raise ValueError(
                f"Permission level '{value}' is invalid; expected one of {sorted(ALLOWED_PERMISSION_LEVELS)}"
            )
        return normalised


class AppConfig(BaseModel):
    platform_name: str = "CommonGraph"
    platform_tagline: str = Field(
        default="Building graph-based collaborative platforms together."
    )
    platform_description: str = ""
    license: str | None = None
    node_types: Dict[str, NodeTypeConfig]
    edge_types: Dict[str, EdgeTypeConfig]
    polls: Dict[str, PollConfig] = Field(default_factory=dict)
    auth: AuthConfig = AuthConfig()
    permissions: PermissionsConfig = PermissionsConfig()
    config_version: str = "1.0.0"

    model_config = ConfigDict(extra="allow")

    @field_validator("platform_tagline", mode="before")
    def prefer_tagline(cls, value, info: FieldValidationInfo):
        if value:
            return value
        tagline = info.data.get("tagline")
        if tagline:
            return tagline
        return "Building graph-based collaborative platforms together."

    @field_validator("platform_description", mode="before")
    def prefer_description(cls, value, info: FieldValidationInfo):
        if value:
            return value
        description_html = info.data.get("description_html")
        if description_html:
            return description_html
        return ""

    @field_validator("license")
    def strip_license(cls, value):
        if value is None:
            return None
        trimmed = value.strip()
        return trimmed or None

    @root_validator(skip_on_failure=True)
    def check_references(cls, values):
        node_types = set(values.get("node_types", {}).keys())
        edge_types = values.get("edge_types", {})
        for edge_name, edge_def in edge_types.items():
            for source, target in edge_def.between:
                if source not in node_types or target not in node_types:
                    raise ValueError(
                        f"Edge '{edge_name}' references unknown node types in 'between': "
                        f"{source} -> {target}"
                    )
        polls = values.get("polls", {})
        for poll_name, poll in polls.items():
            for node_type in poll.node_types:
                if node_type not in node_types:
                    raise ValueError(
                        f"Poll '{poll_name}' references unknown node type '{node_type}'"
                    )
            for edge_type in poll.edge_types:
                if edge_type not in edge_types:
                    raise ValueError(
                        f"Poll '{poll_name}' references unknown edge type '{edge_type}'"
                    )
        return values


def load_config() -> Dict[str, Any]:
    """Load configuration from YAML file without validation."""
    try:
        contents = _CONFIG_PATH.read_text()
    except OSError as exc:
        raise ConfigError(
            f"Could not read config file at {_CONFIG_PATH}: {exc}"
        ) from exc

    try:
        raw = yaml.safe_load(contents)
    except yaml.YAMLError as exc:
        raise ConfigError(f"Invalid YAML in config file {_CONFIG_PATH}: {exc}") from exc

    if raw is None:
        return {}
    if not isinstance(raw, dict):
        raise ConfigError(
            f"Config file {_CONFIG_PATH} must contain a mapping at the top level"
        )
    return raw


def _load_validated_config() -> AppConfig:
    raw = load_config()
    try:
        return AppConfig(**raw)
    except ValidationError as exc:
        raise ConfigError(f"Invalid configuration at {_CONFIG_PATH}: {exc}") from exc


def get_current_config() -> Dict[str, Any]:
    """Get the current configuration (reloads from file and validates)."""
    return _load_validated_config().model_dump()


# Initial load for backward compatibility
_CONFIG_MODEL = _load_validated_config()
_CONFIG = _CONFIG_MODEL.model_dump()

PLATFORM_NAME = _CONFIG_MODEL.platform_name
PLATFORM_TAGLINE = _CONFIG_MODEL.platform_tagline
PLATFORM_DESCRIPTION = _CONFIG_MODEL.platform_description
LICENSE = _CONFIG_MODEL.license
NODE_TYPE_CFG = _CONFIG["node_types"]
EDGE_TYPE_CFG = _CONFIG["edge_types"]
POLLS_CFG = _CONFIG.get("polls", {})

# 6. Authentication configuration
AUTH_CFG = _CONFIG["auth"]
ALLOW_SIGNUP = _CONFIG_MODEL.auth.allow_signup
SIGNUP_REQUIRES_ADMIN_APPROVAL = _CONFIG_MODEL.auth.signup_requires_admin_approval
SIGNUP_REQUIRES_TOKEN = _CONFIG_MODEL.auth.signup_requires_token

# 7. Permissions configuration
PERMISSIONS_CFG = _CONFIG["permissions"]
PERMISSION_READ = _CONFIG_MODEL.permissions.read
PERMISSION_CREATE = _CONFIG_MODEL.permissions.create
PERMISSION_EDIT = _CONFIG_MODEL.permissions.edit
PERMISSION_DELETE = _CONFIG_MODEL.permissions.delete
PERMISSION_RATE = _CONFIG_MODEL.permissions.rate

# 2. Build maps for properties
NODE_TYPE_PROPS = {
    nt: set(defn.get("properties", [])) for nt, defn in NODE_TYPE_CFG.items()
}
EDGE_TYPE_PROPS = {
    et: set(defn.get("properties", [])) for et, defn in EDGE_TYPE_CFG.items()
}

# 3. Build maps for styles
NODE_TYPE_STYLE = {nt: defn.get("style", {}) for nt, defn in NODE_TYPE_CFG.items()}
EDGE_TYPE_STYLE = {et: defn.get("style", {}) for et, defn in EDGE_TYPE_CFG.items()}

# 4. between specifics for graph schema
EDGE_TYPE_BETWEEN = {
    et: defn.get("between", None) for et, defn in EDGE_TYPE_CFG.items()
}

# 5. Polls configuration


def get_node_type_polls() -> dict:
    """Return the polls configuration per node or edge type."""
    out = {k: {} for k in NODE_TYPE_CFG}
    for k, v in POLLS_CFG.items():
        for tp in v.get("node_types", []):
            out[tp][k] = v
    return out


def get_edge_type_polls() -> dict:
    """Return the polls configuration per edge type."""
    out = {k: {} for k in EDGE_TYPE_CFG}
    for k, v in POLLS_CFG.items():
        for tp in v.get("edge_types", []):
            out[tp][k] = v
    return out


NODE_TYPE_POLLS = get_node_type_polls()
EDGE_TYPE_POLLS = get_edge_type_polls()

# Schema versioning configuration
def _compute_config_hash(config: Dict[str, Any]) -> str:
    """Compute hash of the configuration for change detection"""
    config_str = json.dumps(config, sort_keys=True)
    return hashlib.sha256(config_str.encode()).hexdigest()


def _get_config_version(config: Dict[str, Any]) -> str:
    """Extract version from config or generate one"""
    return config.get("config_version", "1.0.0")


def get_current_config_hash() -> str:
    """Get hash of current config (reloads from file)"""
    return _compute_config_hash(get_current_config())


def get_current_config_version() -> str:
    """Get version based on config hash (short, readable)"""
    full_hash = get_current_config_hash()
    # Use first 12 characters of hash as version
    return f"v{full_hash[:12]}"


# Initial values for backward compatibility
CONFIG_HASH = _compute_config_hash(_CONFIG)
CONFIG_VERSION = _get_config_version(_CONFIG)


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
            changes.append(
                {
                    "type": "add_node_type",
                    "node_type": added,
                    "properties": new_config["node_types"][added].get("properties", []),
                }
            )

        for removed in old_nodes - new_nodes:
            changes.append(
                {
                    "type": "remove_node_type",
                    "node_type": removed,
                    "warning": "This will affect existing nodes of this type",
                }
            )

        # Check property changes for existing node types
        for node_type in old_nodes & new_nodes:
            old_props = set(old_config["node_types"][node_type].get("properties", []))
            new_props = set(new_config["node_types"][node_type].get("properties", []))

            for added_prop in new_props - old_props:
                changes.append(
                    {
                        "type": "add_node_property",
                        "node_type": node_type,
                        "property": added_prop,
                    }
                )

            for removed_prop in old_props - new_props:
                changes.append(
                    {
                        "type": "remove_node_property",
                        "node_type": node_type,
                        "property": removed_prop,
                        "warning": "This will affect existing node data",
                    }
                )

        # Check edge type changes
        old_edges = set(old_config.get("edge_types", {}).keys())
        new_edges = set(new_config.get("edge_types", {}).keys())

        for added in new_edges - old_edges:
            changes.append(
                {
                    "type": "add_edge_type",
                    "edge_type": added,
                    "properties": new_config["edge_types"][added].get("properties", []),
                }
            )

        for removed in old_edges - new_edges:
            changes.append(
                {
                    "type": "remove_edge_type",
                    "edge_type": removed,
                    "warning": "This will affect existing edges of this type",
                }
            )

        # Check property changes for existing edge types
        for edge_type in old_edges & new_edges:
            old_props = set(old_config["edge_types"][edge_type].get("properties", []))
            new_props = set(new_config["edge_types"][edge_type].get("properties", []))

            for added_prop in new_props - old_props:
                changes.append(
                    {
                        "type": "add_edge_property",
                        "edge_type": edge_type,
                        "property": added_prop,
                    }
                )

            for removed_prop in old_props - new_props:
                changes.append(
                    {
                        "type": "remove_edge_property",
                        "edge_type": edge_type,
                        "property": removed_prop,
                        "warning": "This will affect existing edge data",
                    }
                )

            # Check for changes in 'between' constraints (critical for graph schema)
            old_between = old_config["edge_types"][edge_type].get("between", [])
            new_between = new_config["edge_types"][edge_type].get("between", [])

            if old_between != new_between:
                changes.append(
                    {
                        "type": "change_edge_between",
                        "edge_type": edge_type,
                        "old_between": old_between,
                        "new_between": new_between,
                        "warning": "Changing 'between' constraints will affect edge creation rules and may invalidate existing edges",
                    }
                )

        # Check poll changes
        old_polls = set(old_config.get("polls", {}).keys())
        new_polls = set(new_config.get("polls", {}).keys())

        for added in new_polls - old_polls:
            changes.append({"type": "add_poll", "poll": added})

        for removed in old_polls - new_polls:
            changes.append(
                {
                    "type": "remove_poll",
                    "poll": removed,
                    "warning": "This will affect existing ratings",
                }
            )

        # Check for changes in existing polls (options, node_types, edge_types, scale)
        for poll_name in old_polls & new_polls:
            old_poll = old_config["polls"][poll_name]
            new_poll = new_config["polls"][poll_name]

            # Check scale changes
            old_scale = old_poll.get("scale")
            new_scale = new_poll.get("scale")
            if old_scale != new_scale:
                changes.append(
                    {
                        "type": "change_poll_scale",
                        "poll": poll_name,
                        "old_scale": old_scale,
                        "new_scale": new_scale,
                        "warning": "Changing poll scale may invalidate existing ratings",
                    }
                )

            # Check options changes (for discrete polls)
            old_options = old_poll.get("options", {})
            new_options = new_poll.get("options", {})

            # Normalise both to strings for comparison (YAML might load numbers differently)
            old_options_str = {str(k): str(v) for k, v in old_options.items()}
            new_options_str = {str(k): str(v) for k, v in new_options.items()}

            if old_options_str != new_options_str:
                changes.append(
                    {
                        "type": "change_poll_options",
                        "poll": poll_name,
                        "old_options": old_options,
                        "new_options": new_options,
                        "warning": "Changing poll options may invalidate existing ratings",
                    }
                )

            # Check range changes (for continuous polls)
            old_range = old_poll.get("range")
            new_range = new_poll.get("range")
            if old_range != new_range:
                changes.append(
                    {
                        "type": "change_poll_range",
                        "poll": poll_name,
                        "old_range": old_range,
                        "new_range": new_range,
                        "warning": "Changing poll range may invalidate existing ratings",
                    }
                )

            # Check node_types changes
            old_node_types = set(old_poll.get("node_types", []))
            new_node_types = set(new_poll.get("node_types", []))
            if old_node_types != new_node_types:
                removed_types = old_node_types - new_node_types
                added_types = new_node_types - old_node_types
                changes.append(
                    {
                        "type": "change_poll_node_types",
                        "poll": poll_name,
                        "removed_node_types": list(removed_types),
                        "added_node_types": list(added_types),
                        "warning": f"Changing applicable node types may affect existing ratings on nodes",
                    }
                )

            # Check edge_types changes
            old_edge_types = set(old_poll.get("edge_types", []))
            new_edge_types = set(new_poll.get("edge_types", []))
            if old_edge_types != new_edge_types:
                removed_types = old_edge_types - new_edge_types
                added_types = new_edge_types - old_edge_types
                changes.append(
                    {
                        "type": "change_poll_edge_types",
                        "poll": poll_name,
                        "removed_edge_types": list(removed_types),
                        "added_edge_types": list(added_types),
                        "warning": f"Changing applicable edge types may affect existing ratings on edges",
                    }
                )

            # Check aggregation method changes
            old_aggregation = old_poll.get("aggregation")
            new_aggregation = new_poll.get("aggregation")
            if old_aggregation != new_aggregation:
                changes.append(
                    {
                        "type": "change_poll_aggregation",
                        "poll": poll_name,
                        "old_aggregation": old_aggregation,
                        "new_aggregation": new_aggregation,
                        "warning": "Changing aggregation method will affect computed poll results",
                    }
                )

        return changes

    @staticmethod
    def validate_against_existing_data(changes: List[Dict], session) -> List[str]:
        """Validate changes against existing database data"""
        warnings = []

        try:
            for change in changes:
                if change["type"] == "remove_node_type":
                    # Check if nodes of this type exist
                    from sqlmodel import text

                    stmt = text(
                        "SELECT COUNT(*) FROM graphhistoryevent WHERE entity_type = 'node' AND payload->>'node_type' = :node_type AND state != 'deleted'"
                    )
                    result = session.execute(
                        stmt, {"node_type": change["node_type"]}
                    ).scalar()
                    if result and result > 0:
                        warnings.append(
                            f"Removing node type '{change['node_type']}' will affect {result} existing nodes"
                        )

                elif change["type"] == "remove_edge_type":
                    # Check if edges of this type exist
                    from sqlmodel import text

                    stmt = text(
                        "SELECT COUNT(*) FROM graphhistoryevent WHERE entity_type = 'edge' AND payload->>'edge_type' = :edge_type AND state != 'deleted'"
                    )
                    result = session.execute(
                        stmt, {"edge_type": change["edge_type"]}
                    ).scalar()
                    if result and result > 0:
                        warnings.append(
                            f"Removing edge type '{change['edge_type']}' will affect {result} existing edges"
                        )

                elif change["type"] == "change_edge_between":
                    # Check if edges of this type exist that might violate new constraints
                    from sqlmodel import text

                    stmt = text(
                        "SELECT COUNT(*) FROM graphhistoryevent WHERE entity_type = 'edge' AND payload->>'edge_type' = :edge_type AND state != 'deleted'"
                    )
                    result = session.execute(
                        stmt, {"edge_type": change["edge_type"]}
                    ).scalar()
                    if result and result > 0:
                        warnings.append(
                            f"Changing 'between' constraints for '{change['edge_type']}' may invalidate {result} existing edges"
                        )

                elif change["type"] in [
                    "change_poll_scale",
                    "change_poll_options",
                    "change_poll_range",
                ]:
                    # Check if ratings exist for this poll
                    from sqlmodel import text

                    stmt = text(
                        "SELECT COUNT(*) FROM ratingevent WHERE poll_label = :poll_label"
                    )
                    result = session.execute(
                        stmt, {"poll_label": change["poll"]}
                    ).scalar()
                    if result and result > 0:
                        warnings.append(
                            f"Changing poll '{change['poll']}' configuration will affect {result} existing ratings"
                        )

                elif change["type"] == "change_poll_node_types":
                    # Check if ratings exist on nodes of removed types
                    removed_types = change.get("removed_node_types", [])
                    if removed_types:
                        from sqlmodel import text

                        for node_type in removed_types:
                            stmt = text(
                                """
                                SELECT COUNT(*) FROM ratingevent r
                                JOIN graphhistoryevent n ON r.node_id = n.node_id
                                WHERE r.poll_label = :poll_label AND n.payload->>'node_type' = :node_type AND n.state != 'deleted'
                            """
                            )
                            result = session.execute(
                                stmt,
                                {"poll_label": change["poll"], "node_type": node_type},
                            ).scalar()
                            if result and result > 0:
                                warnings.append(
                                    f"Removing node type '{node_type}' from poll '{change['poll']}' will affect {result} existing ratings"
                                )

                elif change["type"] == "change_poll_edge_types":
                    # Check if ratings exist on edges of removed types
                    removed_types = change.get("removed_edge_types", [])
                    if removed_types:
                        from sqlmodel import text

                        for edge_type in removed_types:
                            stmt = text(
                                """
                                SELECT COUNT(*) FROM ratingevent r
                                JOIN graphhistoryevent e ON r.source_id = e.payload->>'source' AND r.target_id = e.payload->>'target'
                                WHERE r.poll_label = :poll_label AND e.payload->>'edge_type' = :edge_type AND e.state != 'deleted'
                            """
                            )
                            result = session.execute(
                                stmt,
                                {"poll_label": change["poll"], "edge_type": edge_type},
                            ).scalar()
                            if result and result > 0:
                                warnings.append(
                                    f"Removing edge type '{edge_type}' from poll '{change['poll']}' will affect {result} existing ratings"
                                )

                elif change["type"] == "remove_node_property":
                    warnings.append(
                        f"Removing property '{change['property']}' from '{change['node_type']}' will lose data"
                    )

                elif change["type"] == "remove_edge_property":
                    warnings.append(
                        f"Removing property '{change['property']}' from '{change['edge_type']}' will lose data"
                    )

        except Exception as e:
            # If database queries fail, just return basic warnings
            warnings.append(f"Could not validate against existing data: {str(e)}")

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

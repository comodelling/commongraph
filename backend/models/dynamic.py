import datetime
import logging
from typing import Any, Dict, Type, Union

from pydantic import create_model, Field
from sqlmodel import SQLModel

from backend.models.base import NodeBase, EdgeBase, SubgraphBase, GraphExportBase
from backend.properties import PredefinedProperties
from backend.config import NODE_TYPE_PROPS, EDGE_TYPE_PROPS

logger = logging.getLogger(__name__)


def _make_dynamic(
    base: Type[SQLModel],
    props_map: Dict[str, set[str]],
) -> Dict[str, Type[SQLModel]]:
    out: Dict[str, Type[SQLModel]] = {}
    for type_name, allowed in props_map.items():
        fields: dict[str, tuple[Any, Any]] = {}
        # Include fields defined on the base model.
        for f, md in base.model_fields.items():
            anno = md.annotation
            if f in ["node_type", "edge_type"]:
                fields[f] = (anno, type_name)
            elif f in allowed:
                raise ValueError(f"{f} is reserved and cannot be dynamically set.")
            else:
                anno = md.annotation
                if hasattr(md, "default_factory") and md.default_factory is not None:
                    default = md.default_factory()
                elif md.default is not Ellipsis:
                    default = md.default
                else:
                    default = ...
                fields[f] = (anno, default)
        # If the base is NodeBase, include extra rich properties from RichNodeProperties when allowed.
        for f, md in PredefinedProperties.model_fields.items():
            if f in allowed:
                anno = md.annotation
                if hasattr(md, "default_factory") and md.default_factory is not None:
                    default = md.default_factory()
                elif md.default is not Ellipsis:
                    default = md.default
                else:
                    default = ...
                fields[f] = (anno, default)

        name = f"{type_name.title()}{base.__name__}"
        out[type_name] = create_model(name, __base__=base, **fields)
        logger.info(f"Dynamic model created: {name}, fields: {list(fields.keys())}")
    return out


NodeTypeModels = _make_dynamic(NodeBase, NODE_TYPE_PROPS)
EdgeTypeModels = _make_dynamic(EdgeBase, EDGE_TYPE_PROPS)

logger.debug(f"Dynamic node models: {NodeTypeModels}")
logger.debug(f"Dynamic edge models: {EdgeTypeModels}")


DynamicNode = Union[tuple(NodeTypeModels.values())]
DynamicEdge = Union[tuple(EdgeTypeModels.values())]


class DynamicSubgraph(SubgraphBase):
    """Subgraph model with dynamic node and edge types."""
    nodes: list[DynamicNode]   # type: ignore
    edges: list[DynamicEdge]   # type: ignore


class DynamicGraphExport(GraphExportBase):
    """Graph Export model with dynamic node and edge types."""
    schema_version: str = Field(..., description="Schema version used for this export")
    schema_hash: str = Field(..., description="Hash of the schema configuration")
    nodes: list[DynamicNode]   # type: ignore
    edges: list[DynamicEdge]   # type: ignore


class NodeSearchResult(NodeBase, SQLModel):  # not allowed to inherit from DynamicNode
    last_modified: datetime.datetime = Field(
        ..., description="When this node was last updated"
    )
    class Config:
        extra = "allow"   # accept all DynamicNode fields
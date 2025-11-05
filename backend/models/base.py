import datetime
from pydantic import model_validator
from sqlmodel import SQLModel

from backend.config import valid_edge_types, valid_node_types
from backend.models.fixed import NodeId


class NodeBase(SQLModel):
    """Base Node model"""

    node_id: NodeId | None = None  # node id is not created by client
    node_type: str

    @model_validator(mode="before")
    def check_node_type(cls, values):
        # if we’re already dealing with a built model, skip this validator:
        if not isinstance(values, dict):
            return values
        nt = values.get("node_type")
        if nt and nt not in valid_node_types():
            raise ValueError(f"{nt!r} not in configured node_types")
        return values


class PartialNodeBase(NodeBase):
    """Partial Node model
    None here might mean that the field is not present in the request
    """

    node_id: NodeId
    node_type: str | None = None


class EdgeBase(SQLModel):
    """Base Edge model"""

    edge_type: str
    source: NodeId
    target: NodeId

    @model_validator(mode="before")
    def check_edge_type(cls, values):
        if not isinstance(values, dict):
            return values
        et = values.get("edge_type")
        if et and et not in valid_edge_types():
            raise ValueError(f"{et!r} not in configured edge_types")
        return values


class PartialEdgeBase(EdgeBase):
    edge_type: str | None = None


class SubgraphBase(SQLModel):
    """Subgraph model"""

    nodes: list[NodeBase | dict]
    edges: list[EdgeBase | dict]


class GraphExportBase(SQLModel):
    """G Export model"""

    commongraph_version: str
    timestamp: datetime.datetime
    nodes: list[NodeBase | dict]
    edges: list[EdgeBase | dict]

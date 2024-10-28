from typing import Optional, Annotated
from enum import Enum

from fastapi import Path
from pydantic import BaseModel


NodeId = Annotated[
    int,
    Path(
        title="the node ID",
        # alias="node-id",
        ge=0,
    ),
]

EdgeId = Annotated[
    int,
    Path(
        title="the edge ID",
        # alias="edge-id",
        ge=0,
    ),
]


class NodeType(str, Enum):
    undefined = "undefined"
    wish = "wish"
    proposal = "proposal"
    citw = "citw"


class EdgeType(str, Enum):
    condition = "condition"
    implication = "implication"


class Node(BaseModel):
    node_type: NodeType = NodeType.undefined
    summary: str
    description: str = None
    node_id: NodeId = None  # TODO: check whether this could lead to issues if argument passed in create for example


class Edge(BaseModel):
    edge_type: EdgeType
    source: NodeId
    target: NodeId
    # TODO: check whether this could lead to issues if argument passed in create for example
    edge_id: EdgeId = None


class NodeSearch(BaseModel):
    node_type: str = None
    summary: Optional[str] = None
    description: Optional[str] = None

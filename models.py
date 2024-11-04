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


class NodeType(str, Enum):
    change = "change"
    wish = "wish"
    proposal = "proposal"


class EdgeType(str, Enum):
    require = "require"
    imply = "imply"


class NodeBase(BaseModel):
    node_type: NodeType = NodeType.change
    title: str
    scope: str = None
    description: str = None
    node_id: NodeId = None  # TODO: check whether this could lead to issues if argument passed in create for example
    # TODO: add gradable and grade
    # TODO: add history


class EdgeBase(BaseModel):
    edge_type: EdgeType
    source: NodeId
    target: NodeId
    cprob: float = None
    metadata: dict = None

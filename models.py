from typing import Annotated
from enum import Enum

import numpy as np
from pydantic import BaseModel, field_validator
from fastapi import Path, Query
from pydantic import BaseModel


NodeId = Annotated[
    int,
    Path(
        title="the node ID",
        # alias="node-id",
        ge=0,
    ),
]

Proba = Annotated[float, Query(title="conditional proba", ge=0, le=1)]


class NodeType(str, Enum):
    change = "change"
    wish = "wish"
    proposal = "proposal"


class EdgeType(str, Enum):
    require = "require"
    imply = "imply"


class QualitativeGrade(str, Enum):
    A = "A"
    B = "B"
    C = "C"
    D = "D"
    E = "E"


class NodeBase(BaseModel):
    node_type: NodeType = NodeType.change
    title: str
    scope: str | None = None
    description: str | None = None
    node_id: NodeId | None = None  # TODO: check whether this could lead to issues if argument passed in create for example
    id_from_ui: int | None = None
    gradable: bool = False
    grade: QualitativeGrade | None = None
    proponents: list[str] = []
    references: list[str] = []
    # TODO: add history


class EdgeBase(BaseModel):
    edge_type: EdgeType
    source: NodeId
    target: NodeId
    cprob: Proba | None = None
    source_from_ui: int | None = None
    target_from_ui: int | None = None
    references: list[str] = []

    @field_validator("cprob")
    def convert_nan_to_none(cls, v):
        if v is None or (isinstance(v, float) and np.isnan(v)):
            return None
        return v


class Network(BaseModel):
    nodes: list[NodeBase]
    edges: list[EdgeBase]

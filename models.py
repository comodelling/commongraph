from typing import Annotated
from enum import Enum
import math

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
    objective = "objective"
    action = "action"
    potentiality = "potentiality"
    change = "change"
    wish = "wish"  # TODO: depreacate?
    proposal = "proposal"  # TODO: deprecate?

    @classmethod
    def _missing_(cls, value):
        value = value.lower()
        for member in cls:
            if member.value == value:
                return member
        raise ValueError(f"{value} is not a valid {cls.__name__}")


class EdgeType(str, Enum):
    require = "require"
    imply = "imply"


class QualitativeGrade(str, Enum):
    A = "A"
    B = "B"
    C = "C"
    D = "D"
    E = "E"


class NodeStatus(str, Enum):
    unspecified = "unspecified"
    draft = "draft"
    live = "live"
    completed = "completed"
    legacy = "legacy"

    @classmethod
    def _missing_(cls, value):
        value = value.lower()
        for member in cls:
            if member.value == value:
                return member
        raise ValueError(f"{value} is not a valid {cls.__name__}")


class NodeBase(BaseModel):
    node_type: NodeType = NodeType.potentiality
    title: str
    scope: str = None
    status: NodeStatus | None = "unspecified"
    description: str | None = None
    # TODO: check whether this could lead to issues if argument passed in create for example
    node_id: NodeId | None = None
    tags: list[str] = []
    references: list[str] = []
    # TODO: add history

    # deprecated
    id_from_ui: int | None = None
    gradable: bool | None = False
    grade: QualitativeGrade | None = None
    proponents: list[str] = []


class PartialNodeBase(NodeBase):
    node_id: NodeId
    node_type: NodeType | None = None
    title: str | None = None
    scope: str | None = None
    status: NodeStatus | None = None
    tags: list[str] | None = None
    references: list[str] | None = None
    description: str | None = None


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
        if v is None or (isinstance(v, float) and math.isnan(v)):
            return None
        return v


class Network(BaseModel):
    nodes: list[NodeBase]
    edges: list[EdgeBase]

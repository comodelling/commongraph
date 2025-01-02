from typing import Annotated
from enum import Enum
import math

from pydantic import BaseModel, field_validator
from fastapi import Path, Query


NodeId = Annotated[
    int,
    Path(
        title="the node ID",
        ge=0,
    ),
]

Proba = Annotated[float, Query(title="conditional proba", ge=0, le=1)]


class NodeType(str, Enum):
    objective = "objective"
    action = "action"
    potentiality = "potentiality"

    change = "change"  # TODO: migrate and deprecate
    wish = "wish"  # TODO: migrate and deprecate
    proposal = "proposal"  # TODO: migrate and deprecate?

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
    unspecified = "unspecified"  # default
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
    """Base Node model"""

    node_type: NodeType = NodeType.potentiality
    title: str
    scope: str
    status: NodeStatus | None = NodeStatus.unspecified
    description: str | None = None
    node_id: NodeId | None = None
    tags: list[str] = []
    references: list[str] = []
    grade: QualitativeGrade | None = None

    # deprecated
    id_from_ui: int | None = None
    gradable: bool | None = False
    proponents: list[str] = []


class PartialNodeBase(NodeBase):
    """Partial Node model"""

    node_id: NodeId
    node_type: NodeType | None = None
    title: str | None = None
    scope: str | None = None
    status: NodeStatus | None = None
    tags: list[str] | None = None
    references: list[str] | None = None
    description: str | None = None


class EdgeBase(BaseModel):
    """Base Edge model"""

    edge_type: EdgeType
    source: NodeId
    target: NodeId
    cprob: Proba | None = None
    source_from_ui: int | None = None
    target_from_ui: int | None = None
    references: list[str] = []
    description: str | None = None

    @field_validator("cprob")
    def convert_nan_to_none(cls, v):
        if v is None or (isinstance(v, float) and math.isnan(v)):
            return None
        return v


class Subnet(BaseModel):
    """Subnet model"""

    nodes: list[NodeBase]
    edges: list[EdgeBase]

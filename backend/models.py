import warnings
from typing import Annotated, Dict, Set
from enum import Enum

from pydantic import BaseModel, Field, field_validator, model_validator
from fastapi import Query


NodeId = Annotated[
    int,
    Field(
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
    imply = "imply"

    require = "require"


class LikertScale(str, Enum):
    a = "A"  # strongly agree
    b = "B"  # agree
    c = "C"  # neutral
    d = "D"  # disagree
    e = "E"  # strongly disagree


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

    # definition
    node_id: NodeId | None = None  # node id is not created by client
    node_type: NodeType = NodeType.potentiality
    title: str
    scope: str
    status: NodeStatus | None = NodeStatus.unspecified
    description: str | None = None
    tags: list[str] | None = Field(default_factory=list)
    references: list[str] | None = Field(default_factory=list, alias="references")

    # measures
    support: LikertScale | None = None

    # deprecated
    grade: LikertScale | None = Field(None, deprecated=True)
    gradable: bool | None = Field(None, deprecated=True)
    proponents: list[str] | None = Field(default_factory=list, deprecated=True)

    @model_validator(mode="before")
    def handle_deprecated_fields(cls, values):
        if "grade" in values:
            warnings.warn(
                "`grade` field is deprecated and will be removed in future versions. "
                "Please use `support` instead.",
                DeprecationWarning,
            )
            values["support"] = values.pop("grade")
        return values

    @field_validator("gradable")
    def convert_gradable(cls, v):
        return None

    @field_validator("proponents")
    def convert_proponents(cls, v):
        return v

    @classmethod
    def get_single_field_types(cls) -> Dict[str, type]:
        """List of fields encoded as properties with 'single' cardinality in the graph.
        These do not include ID or index related fields: node_id"""
        return {
            "node_type": str,
            "title": str,
            "scope": str,
            "status": str,
            "description": str,
            "support": str,
            # deprecated
            "gradable": bool,
        }

    @classmethod
    def get_list_field_types(cls) -> Dict[str, type]:
        """List of fields encoded as properties with 'list' cardinality in the graph."""
        return {
            "references": list[str],
            "tags": list[str],
            # deprecated
            "proponents": list[str],
        }

    @classmethod
    def get_field_types(cls) -> Dict[str, type]:
        """List of fields to be encoded as properties in the graph."""
        return cls.get_single_field_types() | cls.get_list_field_types()


class PartialNodeBase(NodeBase):
    """Partial Node model
    None here might mean that the field is not present in the request
    """

    node_id: NodeId
    node_type: NodeType | None = None
    title: str | None = None
    scope: str | None = None
    status: NodeStatus | None = None
    tags: list[str] | None = None
    references: list[str] | None = None
    description: str | None = None
    support: LikertScale | None = None


class EdgeBase(BaseModel):
    """Base Edge model"""

    # definition
    edge_type: EdgeType
    source: NodeId
    target: NodeId
    references: list[str] | None = Field(default_factory=list)
    description: str | None = None

    # measures
    causal_strength: Proba | None = None
    causal_strength_rating: LikertScale | None = None
    necessity: Proba | None = None
    neccessity_rating: LikertScale | None = None
    sufficiency: Proba | None = None
    sufficiency_rating: LikertScale | None = None

    # deprecated
    # now in sufficiency for 'imply' and necessity for 'require'
    cprob: Proba | None = Field(None, deprecated=True)
    source_from_ui: int | None = Field(None, deprecated=True)
    target_from_ui: int | None = Field(None, deprecated=True)

    @model_validator(mode="before")
    def convert_cprob(cls, values):
        edge_type = values.get("edge_type")
        cprob = values.get("cprob")
        if cprob is not None:
            if edge_type == EdgeType.require:
                values["necessity"] = cprob
                values["source"], values["target"] = values["target"], values["source"]
                values["edge_type"] = EdgeType.imply
            elif edge_type == EdgeType.imply:
                values["sufficiency"] = cprob
            # Optionally remove the deprecated field
            del values["cprob"]
        return values  # Return the modified values

    @classmethod
    def get_single_field_types(cls) -> Dict[str, type]:
        """List of fields encoded as properties with 'single' cardinality in the graph.
        These do not include ID or index related fields: source, target, edge_type
        """
        return {
            "description": str,
            "causal_strength": float,
            "causal_strength_rating": str,
            "necessity": float,
            "neccessity_rating": str,
            "sufficiency": float,
            "sufficiency_rating": str,
            # deprecated
            "cprob": float,
            "source_from_ui": int,
            "target_from_ui": int,
        }

    @classmethod
    def get_list_field_types(cls) -> Dict[str, type]:
        """List of fields encoded as properties with 'list' cardinality in the graph."""
        return {
            "references": list[str],
        }

    @classmethod
    def get_field_types(cls) -> Dict[str, type]:
        """List of fields to be encoded as properties in the graph."""
        return cls.get_single_field_types() | cls.get_list_field_types()


class PartialEdgeBase(EdgeBase):
    references: list[str] | None = None
    edge_type: EdgeType | None = None


class Subnet(BaseModel):
    """Subnet model"""

    nodes: list[NodeBase]
    edges: list[EdgeBase]

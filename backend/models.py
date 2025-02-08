import warnings
from typing import Annotated, Dict, Any
from enum import Enum
import datetime

from pydantic import model_validator
from fastapi import Query
from sqlalchemy import JSON, Column
from sqlmodel import SQLModel, Field


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


class NodeBase(SQLModel):
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

    # deprecated fields
    grade: LikertScale | None = Field(None, exclude=True)
    gradable: bool | None = Field(None, exclude=True)
    proponents: list[str] | None = Field(default_factory=list, exclude=True)

    @model_validator(mode="before")
    def handle_deprecated_fields(cls, values):
        if "grade" in values:
            warnings.warn(
                "`grade` field is deprecated and will be removed in future versions. "
                "Please use `support` instead.",
                DeprecationWarning,
            )
            if "support" in values:
                warnings.warn("Both `grade` and `support` fields are present.")
            if values["grade"] is not None and (
                "support" not in values or values["support"] is None
            ):
                values["support"] = values["grade"]
        return values

    @classmethod
    def get_single_field_types(cls, deprecated: bool = False) -> Dict[str, type]:
        """List of fields encoded as properties with 'single' cardinality in the graph.
        These do not include ID or index related fields: node_id"""
        fields = {
            "node_type": str,
            "title": str,
            "scope": str,
            "status": str,
            "description": str,
            "support": str,
            "gradable": bool,
        }
        if not deprecated:
            for field in cls.get_deprecated_fields():
                fields.pop(field, None)
        return fields

    @classmethod
    def get_list_field_types(cls, deprecated: bool = False) -> Dict[str, type]:
        """List of fields encoded as properties with 'list' cardinality in the graph."""
        fields = {
            "references": list[str],
            "tags": list[str],
            "proponents": list[str],
        }
        if not deprecated:
            for field in cls.get_deprecated_fields():
                fields.pop(field, None)
        return fields

    @classmethod
    def get_field_types(cls, deprecated: bool = False) -> Dict[str, type]:
        """List of fields to be encoded as properties in the graph."""
        return cls.get_single_field_types(deprecated) | cls.get_list_field_types(
            deprecated
        )

    @classmethod
    def get_deprecated_fields(cls) -> list[str]:
        return [name for name, field in cls.model_fields.items() if field.exclude]


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


class EdgeBase(SQLModel):
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
    cprob: Proba | None = Field(None, exclude=True)
    source_from_ui: int | None = Field(None, exclude=True)
    target_from_ui: int | None = Field(None, exclude=True)

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
        return values  # Return the modified values

    @classmethod
    def get_single_field_types(cls, deprecated: bool = False) -> Dict[str, type]:
        """List of fields encoded as properties with 'single' cardinality in the graph.
        These do not include ID or index related fields: source, target, edge_type
        """
        fields = {
            "description": str,
            "causal_strength": float,
            "causal_strength_rating": str,
            "necessity": float,
            "neccessity_rating": str,
            "sufficiency": float,
            "sufficiency_rating": str,
            "cprob": float,
            "source_from_ui": int,
            "target_from_ui": int,
        }
        if not deprecated:
            for field in cls.get_deprecated_fields():
                fields.pop(field, None)
        return fields

    @classmethod
    def get_list_field_types(cls, deprecated: bool = False) -> Dict[str, type]:
        """List of fields encoded as properties with 'list' cardinality in the graph."""
        fields = {
            "references": list[str],
        }
        if not deprecated:
            for field in cls.get_deprecated_fields():
                fields.pop(field, None)
        return fields

    @classmethod
    def get_field_types(cls, deprecated: bool = False) -> Dict[str, type]:
        """List of fields to be encoded as properties in the graph."""
        return cls.get_single_field_types(deprecated) | cls.get_list_field_types(
            deprecated
        )

    @classmethod
    def get_deprecated_fields(cls) -> list[str]:
        return [name for name, field in cls.model_fields.items() if field.exclude]


class PartialEdgeBase(EdgeBase):
    references: list[str] | None = None
    edge_type: EdgeType | None = None


class Subnet(SQLModel):
    """Subnet model"""

    nodes: list[NodeBase | dict]
    edges: list[EdgeBase | dict]


class MigrateLabelRequest(SQLModel):
    property_name: str


class User(SQLModel, table=True):
    """
    User model for handling user data in the relational database.
    """

    username: str = Field(
        ...,
        primary_key=True,
        index=True,
        description="Unique username for the user",
        min_length=3,
    )
    password: str = Field(..., description="Hashed password for the user", min_length=6)
    preferences: Dict[str, Any] | None = Field(
        default_factory=dict,
        sa_column=Column(JSON),
        description="User's personal preferences",
    )
    security_question: str | None = Field(
        ..., description="Security question for password reset"
    )
    security_answer: str | None = Field(
        ..., description="Answer to the security question"
    )


class UserRead(SQLModel):
    username: str
    preferences: Dict[str, Any] | None = Field(default_factory=dict)


class UserCreate(SQLModel):
    username: str = Field(..., min_length=3)
    password: str = Field(..., min_length=6)
    preferences: Dict[str, Any] | None = Field(default_factory=dict)
    security_question: str | None = Field(
        ..., description="Security question for password reset"
    )
    security_answer: str | None = Field(
        ..., description="Answer to the security question"
    )


class OperationType(str, Enum):
    create = "create"
    update = "update"
    delete = "delete"


class EntityType(str, Enum):
    node = "node"
    edge = "edge"


class GraphHistoryEvent(SQLModel, table=True):
    event_id: int | None = Field(default=None, primary_key=True)
    event_type: OperationType = Field(..., description="Type of operation")
    username: str = Field(
        ..., description="Username of the user who initiated the event"
    )
    node_id: NodeId | None = Field(..., description="ID of the node or edge")
    source_id: NodeId | None = Field(
        None, description="Source node ID for an edge event"
    )
    target_id: NodeId | None = Field(
        None, description="Target node ID for an edge event"
    )
    timestamp: datetime.datetime = Field(
        default_factory=lambda: datetime.datetime.now(datetime.timezone.utc),
        description="Timestamp of the event",
    )
    payload: dict | None = Field(
        default_factory=dict,
        sa_column=Column(JSON),
        description="Payload of the event - for create and update operations",
    )

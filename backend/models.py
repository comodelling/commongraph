from typing import Annotated, Dict, Any
from enum import Enum
import datetime

from pydantic import model_validator
from sqlalchemy import JSON, Column
from sqlmodel import SQLModel, Field

from backend.config import valid_node_types, valid_edge_types
from backend.properties import LikertScale

NodeId = Annotated[
    int,
    Field(
        title="the node ID",
        ge=0,
    ),
]


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


class SubnetBase(SQLModel):
    """Subnet model"""

    nodes: list[NodeBase | dict]
    edges: list[EdgeBase | dict]


class NetworkExportBase(SQLModel):
    """Network Export model"""

    commongraph_version: str
    timestamp: datetime.datetime
    nodes: list[NodeBase | dict]
    edges: list[EdgeBase | dict]


class MigrateLabelRequest(SQLModel):
    property_name: str


class User(SQLModel, table=True):
    """
    User model for handling user data in the relational database.
    """

    __table_args__ = {"extend_existing": True}
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


class EntityState(str, Enum):
    created = "created"
    updated = "updated"
    deleted = "deleted"


class EntityType(str, Enum):
    node = "node"
    edge = "edge"


class GraphHistoryEvent(SQLModel, table=True):
    event_id: int | None = Field(default=None, primary_key=True)
    timestamp: datetime.datetime = Field(
        default_factory=lambda: datetime.datetime.now(datetime.timezone.utc),
        description="Timestamp of the event",
    )
    state: EntityState = Field(
        ..., description="State of the entity (created, updated, deleted)"
    )
    entity_type: EntityType = Field(..., description="Type of entity (node or edge)")
    node_id: NodeId | None = Field(..., description="ID of the node")
    source_id: NodeId | None = Field(None, description="Edge's source node ID")
    target_id: NodeId | None = Field(None, description="Edge's rarget node ID")
    payload: dict | None = Field(
        default_factory=dict,
        sa_column=Column(JSON),
        description="Payload containing the entity's full state",
    )
    username: str = Field(..., description="Username of the user who rated the entity")

    @model_validator(mode="after")
    def check_entity_type_fields(
        cls, values: "GraphHistoryEvent"
    ) -> "GraphHistoryEvent":
        if values.entity_type == EntityType.node and values.node_id is None:
            raise ValueError("For entity_type 'node', node_id must be provided.")
        if values.entity_type == EntityType.edge and (
            values.source_id is None or values.target_id is None
        ):
            raise ValueError(
                "For entity_type 'edge', both source_id and target_id must be provided."
            )
        return values


class RatingType(str, Enum):
    support = "support"
    causal_strength = "causal_strength"
    necessity = "necessity"
    sufficiency = "sufficiency"


class RatingEvent(SQLModel, table=True):
    """RatingEvent model"""

    __table_args__ = {"extend_existing": True}
    event_id: int | None = Field(default=None, primary_key=True)
    entity_type: EntityType = Field(..., description="Type of entity (node or edge)")
    node_id: NodeId | None = Field(..., description="ID of the node")
    source_id: NodeId | None = Field(None, description="Edge's source node ID")
    target_id: NodeId | None = Field(None, description="Edge's rarget node ID")
    rating_type: str = Field(..., description="Type of rating")   #TODO: rename as rating_name?
    rating: LikertScale = Field(..., description="Rating value")  #TODO: allow different types of rating? 
    timestamp: datetime.datetime = Field(
        default_factory=lambda: datetime.datetime.now(datetime.timezone.utc),
        description="Timestamp of the rating",
    )
    username: str = Field(..., description="Username of the user who rated the entity")

    @model_validator(mode="after")
    def check_entity_type_fields(cls, values: "RatingEvent") -> "RatingEvent":
        if values.entity_type == EntityType.node and values.node_id is None:
            raise ValueError("For entity_type 'node', node_id must be provided.")
        if values.entity_type == EntityType.edge and (
            values.source_id is None or values.target_id is None
        ):
            raise ValueError(
                "For entity_type 'edge', both source_id and target_id must be provided."
            )
        return values

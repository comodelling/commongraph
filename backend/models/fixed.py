import datetime
from typing import Annotated, Any, Dict
from enum import Enum

from pydantic import model_validator
from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel

from backend.properties import LikertScale


NodeId = Annotated[
    int,
    Field(
        title="the node ID",
        ge=0,
    ),
]

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


class MigrateLabelRequest(SQLModel):
    property_name: str


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



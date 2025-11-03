import datetime
from typing import Annotated, Any, Dict
from enum import Enum

from pydantic import model_validator
from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel

from backend.config import SIGNUP_REQUIRES_ADMIN_APPROVAL


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
    is_active: bool = Field(
        default=not SIGNUP_REQUIRES_ADMIN_APPROVAL,
        description="User must be approved by an admin before activation"
    )
    is_admin: bool = Field(
        default=False,
        description="Global admin user"
    )
    is_super_admin: bool = Field(
        default=False,
        description="Super admin user with permanent admin rights that cannot be revoked"
    )


class UserRead(SQLModel):
    username: str
    preferences: Dict[str, Any] | None = Field(default_factory=dict)
    is_active: bool
    is_admin: bool
    is_super_admin: bool


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
    is_active: bool = Field(
        default=not SIGNUP_REQUIRES_ADMIN_APPROVAL,
        description="set by admin or signup logic"
    )
    is_admin: bool = Field(
        default=False,
        description="grant admin rights"
    )
    is_super_admin: bool = Field(
        default=False,
        description="grant super admin rights"
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


class Scope(SQLModel, table=True):
    """Scope model for storing geographic/jurisdictional scopes."""
    
    __table_args__ = {"extend_existing": True}
    scope_id: int | None = Field(default=None, primary_key=True)
    name: str = Field(
        ...,
        unique=True,
        index=True,
        description="Unique name of the scope (e.g., 'global', 'France', 'Paris')"
    )
    created_at: datetime.datetime = Field(
        default_factory=lambda: datetime.datetime.now(datetime.timezone.utc),
        description="When this scope was created",
    )


class ScopeRead(SQLModel):
    """Scope read model for API responses."""
    scope_id: int
    name: str
    created_at: datetime.datetime


class ScopeCreate(SQLModel):
    """Scope creation model."""
    name: str = Field(..., min_length=1, description="Name of the scope")


class SignupToken(SQLModel, table=True):
    """SignupToken model for invite-only signups"""

    __table_args__ = {"extend_existing": True}
    token: str = Field(
        ...,
        primary_key=True,
        index=True,
        description="Unique token for signup access"
    )
    created_by: str = Field(..., description="Admin username who created this token")
    created_at: datetime.datetime = Field(
        default_factory=lambda: datetime.datetime.now(datetime.timezone.utc),
        description="When this token was created"
    )
    used_by: str | None = Field(
        default=None,
        description="Username who used this token, if any"
    )
    used_at: datetime.datetime | None = Field(
        default=None,
        description="When this token was used, if at all"
    )
    notes: str | None = Field(
        default=None,
        description="Optional notes about who this token is for"
    )


class SignupTokenRead(SQLModel):
    """SignupToken read model for API responses"""
    token: str
    created_by: str
    created_at: datetime.datetime
    used_by: str | None
    used_at: datetime.datetime | None
    notes: str | None


class SignupTokenCreate(SQLModel):
    """SignupToken creation model"""
    notes: str | None = Field(default=None, description="Optional notes about who this token is for")


class RatingEvent(SQLModel, table=True):
    """RatingEvent model"""

    __table_args__ = {"extend_existing": True}
    event_id: int | None = Field(default=None, primary_key=True)
    entity_type: EntityType = Field(..., description="Type of entity (node or edge)")
    node_id: NodeId | None = Field(..., description="ID of the node")
    source_id: NodeId | None = Field(None, description="Edge's source node ID")
    target_id: NodeId | None = Field(None, description="Edge's target node ID")
    poll_label: str = Field(index=True, description="Must match a key in your configured polls")
    rating: float = Field(description="Discrete or continuous value, interpretation driven by config")
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



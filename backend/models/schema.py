import datetime
from typing import Dict, Any
from sqlmodel import SQLModel, Field
from sqlalchemy import JSON, Column


class GraphSchema(SQLModel, table=True):
    """Store the active graph schema configuration"""
    __table_args__ = {"extend_existing": True}
    
    schema_id: int | None = Field(default=None, primary_key=True)
    version: str = Field(..., description="Schema version (e.g., '1.0.0')")
    config_hash: str = Field(..., description="Hash of the configuration for change detection")
    node_types: Dict[str, Any] = Field(sa_column=Column(JSON))
    edge_types: Dict[str, Any] = Field(sa_column=Column(JSON))
    polls: Dict[str, Any] = Field(sa_column=Column(JSON))
    auth: Dict[str, Any] = Field(sa_column=Column(JSON))
    created_at: datetime.datetime = Field(
        default_factory=lambda: datetime.datetime.now(datetime.timezone.utc),
        description="When this schema version was created"
    )
    is_active: bool = Field(default=True, description="Whether this schema version is active")


class SchemaMigration(SQLModel, table=True):
    """Track schema migrations"""
    __table_args__ = {"extend_existing": True}
    
    migration_id: int | None = Field(default=None, primary_key=True)
    from_version: str = Field(..., description="Previous schema version")
    to_version: str = Field(..., description="New schema version")
    migration_type: str = Field(..., description="add_node_type, remove_property, etc.")
    changes: Dict[str, Any] = Field(sa_column=Column(JSON), description="Detailed changes")
    applied_at: datetime.datetime = Field(
        default_factory=lambda: datetime.datetime.now(datetime.timezone.utc),
        description="When this migration was applied"
    )
    applied_by: str = Field(..., description="Username who applied the migration")

from typing import Annotated
from enum import Enum

from fastapi import Query
from sqlmodel import Field, SQLModel


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
    

class PredefinedProperties(SQLModel):
    title: str | None = None
    scope: str | None = None
    status: NodeStatus | None = NodeStatus.unspecified
    description: str | None = None
    tags: list[str] | None = Field(default_factory=list)
    references: list[str] | None = Field(default_factory=list)

    
Proba = Annotated[float, Query(title="conditional proba", ge=0, le=1)]


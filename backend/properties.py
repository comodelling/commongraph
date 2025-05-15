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


class LikertScale(str, Enum):
    a = "A"  # strongly agree
    b = "B"  # agree
    c = "C"  # neutral
    d = "D"  # disagree
    e = "E"  # strongly disagree

    @classmethod
    def _missing_(cls, value):
        if isinstance(value, str):
            uppercase = value.upper()
            if uppercase in cls._value2member_map_:
                return cls._value2member_map_[uppercase]
        raise ValueError(f"{value} is not a valid {cls.__name__}")
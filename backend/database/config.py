from sqlalchemy import create_engine
from sqlmodel import SQLModel

_engine = None


def get_engine(database_url: str):
    global _engine
    if _engine is None:
        _engine = create_engine(database_url)
        SQLModel.metadata.create_all(_engine)
    return _engine

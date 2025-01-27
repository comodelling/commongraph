from typing import Optional
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
from sqlmodel import SQLModel, Session, select
from fastapi import HTTPException

from .base import UserDatabaseInterface
from models import User, UserRead, UserCreate
from utils.security import hash_password


class PostgreSQLDB(UserDatabaseInterface):
    def __init__(self, database_url: str):
        self.engine = create_engine(database_url)
        SQLModel.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=self.engine
        )

    def create_user(self, user: UserCreate) -> UserRead:
        with Session(self.engine) as session:
            hashed_password = hash_password(user.password)
            db_user = User(
                username=user.username,
                password=hashed_password,
                preferences=user.preferences,
            )
            session.add(db_user)
            try:
                session.commit()
            except IntegrityError:
                session.rollback()
                raise HTTPException(status_code=400, detail="Username already exists")
            session.refresh(db_user)
            return UserRead(username=db_user.username, preferences=db_user.preferences)

    def get_user(self, username: str) -> Optional[UserRead]:
        with Session(self.engine) as session:
            statement = select(User).where(User.username == username)
            result = session.exec(statement).first()
            if result:
                return UserRead(
                    username=result.username, preferences=result.preferences
                )
            return None

    def reset_whole_network(self):
        """Reset the database by dropping all tables and recreating them."""
        SQLModel.metadata.drop_all(self.engine)
        SQLModel.metadata.create_all(self.engine)

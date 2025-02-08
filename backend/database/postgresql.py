from typing import List
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
from sqlmodel import SQLModel, Session, select
from fastapi import HTTPException

from .base import UserDatabaseInterface, GraphHistoryDatabaseInterface
from models import User, UserRead, UserCreate, GraphHistoryEvent
from utils.security import hash_password
from database.config import get_engine


class UserPostgreSQLDB(UserDatabaseInterface):
    def __init__(self, database_url: str):
        super().__init__()
        self.engine = get_engine(database_url)
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
                security_question=user.security_question,
                security_answer=user.security_answer,
            )
            session.add(db_user)
            try:
                session.commit()
                session.refresh(db_user)
            except IntegrityError:
                session.rollback()
                raise HTTPException(status_code=400, detail="User already exists")
            return UserRead(username=db_user.username, preferences=db_user.preferences)

    def get_user(self, username: str) -> User | None:
        with Session(self.engine) as session:
            statement = select(User).where(User.username == username)
            result = session.exec(statement).first()
            return result

    def update_user(self, user: User) -> UserRead:
        with Session(self.engine) as session:
            session.add(user)
            session.commit()
            session.refresh(user)
            return UserRead(username=user.username, preferences=user.preferences)

    def update_preferences(self, username: str, new_prefs: dict) -> UserRead:
        with Session(self.engine) as session:
            statement = select(User).where(User.username == username)
            user = session.exec(statement).first()
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            # Ensure preferences is a dict (or JSON) to update
            if not user.preferences:
                user.preferences = {}
            self.logger.info(f"Current preferences before update: {user.preferences}")
            # user.preferences.update(new_prefs)
            user.preferences = {**user.preferences, **new_prefs}
            self.logger.info(f"New preferences to be updated: {new_prefs}")
            self.logger.info(f"Updated preferences after merge: {user.preferences}")
            session.add(user)
            session.commit()
            session.refresh(user)
            self.logger.info(
                f"Final preferences in database after commit: {user.preferences}"
            )
            return UserRead(username=user.username, preferences=user.preferences)

    def reset_user_table(self):
        """Reset the database by dropping all tables and recreating them."""
        SQLModel.metadata.drop_all(self.engine)
        SQLModel.metadata.create_all(self.engine)


class GraphHistoryPostgreSQLDB(GraphHistoryDatabaseInterface):
    def __init__(self, database_url: str):
        super().__init__()
        self.engine = get_engine(database_url)
        self.SessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=self.engine
        )

    def log_event(self, event: GraphHistoryEvent) -> GraphHistoryEvent:
        with Session(self.engine) as session:
            session.add(event)
            session.commit()
            session.refresh(event)
            self.logger.info(f"Logged event: {event.event_id}")
            return event

    def get_node_history(self, node_id: int) -> List[GraphHistoryEvent]:
        with Session(self.engine) as session:
            statement = select(GraphHistoryEvent).where(
                GraphHistoryEvent.node_id == node_id
            )
            events = session.exec(statement).all()
            self.logger.info(f"Found {len(events)} events for node: {node_id}")
            return events

    def get_edge_history(
        self, source_id: int, target_id: int
    ) -> List[GraphHistoryEvent]:
        with Session(self.engine) as session:
            statement = select(GraphHistoryEvent).where(
                GraphHistoryEvent.source_id == source_id,
                GraphHistoryEvent.target_id == target_id,
            )
            events = session.exec(statement).all()
            self.logger.info(
                f"Found {len(events)} events for edge: {source_id} -> {target_id}"
            )
            return events

    def revert_to_event(self, event_id: int) -> None:
        # Implementation would depend on your event-sourcing mechanism.
        self.logger.info(f"Requested revert to event {event_id}")
        raise HTTPException(
            status_code=501, detail="Revert functionality not implemented yet."
        )

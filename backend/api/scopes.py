import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session, select, func

from backend.db.connections import get_relational_session
from backend.models.fixed import Scope, ScopeRead, ScopeCreate
from backend.api.auth import get_current_user
from backend.models.fixed import UserRead

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/scopes", tags=["scopes"])


@router.get("", response_model=List[ScopeRead])
def search_scopes(
    q: str = Query(None, description="Search query for scope names"),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of results"),
    session: Session = Depends(get_relational_session),
) -> List[Scope]:
    """
    Search for scopes by name. Returns scopes matching the query.
    If no query provided, returns all scopes (up to limit).
    """
    statement = select(Scope)

    if q:
        # Case-insensitive partial match
        statement = statement.where(func.lower(Scope.name).contains(func.lower(q)))

    statement = statement.order_by(Scope.name).limit(limit)
    scopes = session.exec(statement).all()

    return scopes


@router.post("", response_model=ScopeRead, status_code=status.HTTP_201_CREATED)
def create_scope(
    scope_data: ScopeCreate,
    session: Session = Depends(get_relational_session),
    user: UserRead = Depends(get_current_user),
) -> Scope:
    """
    Create a new scope. Requires authentication.
    Returns 409 if scope with this name already exists.
    """
    # Check if scope already exists
    existing = session.exec(
        select(Scope).where(func.lower(Scope.name) == func.lower(scope_data.name))
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Scope with name '{scope_data.name}' already exists",
        )

    # Create new scope
    scope = Scope(name=scope_data.name.strip())
    session.add(scope)
    session.commit()
    session.refresh(scope)

    logger.info(f"User {user.username} created scope: {scope.name}")

    return scope


@router.get("/by-name/{name}", response_model=ScopeRead)
def get_scope_by_name(
    name: str,
    session: Session = Depends(get_relational_session),
) -> Scope:
    """Get a scope by its exact name (case-insensitive)."""
    scope = session.exec(
        select(Scope).where(func.lower(Scope.name) == func.lower(name))
    ).first()

    if not scope:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Scope '{name}' not found"
        )

    return scope


def get_or_create_scope(name: str, session: Session) -> Scope:
    """
    Helper function to get an existing scope by name or create a new one.
    This is used internally by the node creation/update endpoints.
    """
    if not name or not name.strip():
        raise ValueError("Scope name cannot be empty")

    name = name.strip()

    # Try to find existing scope (case-insensitive)
    scope = session.exec(
        select(Scope).where(func.lower(Scope.name) == func.lower(name))
    ).first()

    if scope:
        return scope

    # Create new scope
    scope = Scope(name=name)
    session.add(scope)
    session.flush()  # Get the ID without committing the transaction

    logger.info(f"Auto-created scope: {scope.name}")

    return scope

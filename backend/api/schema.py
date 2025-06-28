from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session
from typing import List

from backend.schema_manager import SchemaManager
from backend.db.connections import get_graph_history_db
from backend.api.auth import get_current_user
from backend.models.fixed import User
from backend.models.schema import GraphSchema, SchemaMigration


router = APIRouter(prefix="/schema", tags=["schema"])


def get_session():
    """Get database session for schema management"""
    db = get_graph_history_db()
    with Session(db.engine) as session:
        yield session


@router.get("/status")
async def get_schema_status(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Get current schema status and check for changes"""
    manager = SchemaManager(session)
    has_changes, changes, warnings = manager.check_for_schema_changes()
    active_schema = manager.get_active_schema()
    
    return {
        "has_changes": has_changes,
        "changes": changes,
        "warnings": warnings,
        "active_schema": {
            "version": active_schema.version if active_schema else None,
            "config_hash": active_schema.config_hash if active_schema else None,
            "created_at": active_schema.created_at if active_schema else None
        } if active_schema else None
    }


@router.post("/apply")
async def apply_schema_changes(
    force: bool = Query(False, description="Apply changes even if there are warnings"),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Apply schema changes from YAML config"""
    if not current_user.is_admin:
        raise HTTPException(403, "Admin access required")
    
    manager = SchemaManager(session)
    try:
        new_schema = manager.apply_schema_update(current_user.username, force)
        return {
            "success": True, 
            "new_version": new_schema.version,
            "message": f"Schema updated to version {new_schema.version}"
        }
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.get("/history", response_model=List[GraphSchema])
async def get_schema_history(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Get all schema versions"""
    if not current_user.is_admin:
        raise HTTPException(403, "Admin access required")
    
    manager = SchemaManager(session)
    return manager.get_schema_history()


@router.get("/migrations", response_model=List[SchemaMigration])
async def get_migrations(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Get all schema migrations"""
    if not current_user.is_admin:
        raise HTTPException(403, "Admin access required")
    
    manager = SchemaManager(session)
    return manager.get_migrations()


@router.post("/initialize")
async def initialize_schema(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Initialize schema in database from current YAML config"""
    if not current_user.is_admin:
        raise HTTPException(403, "Admin access required")
    
    manager = SchemaManager(session)
    schema = manager.ensure_schema_in_db(current_user.username)
    return {
        "success": True,
        "version": schema.version,
        "message": f"Schema initialized with version {schema.version}"
    }

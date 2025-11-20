from fastapi import APIRouter, Depends, Query, status, HTTPException

from backend.api.auth import get_current_user
from backend.db.base import GraphHistoryRelationalInterface
from backend.db.connections import get_graph_history_db
from backend.models.fixed import UserRead
from backend.utils.permissions import can_read


router = APIRouter(prefix="/tags", tags=["tags"])


@router.get("", response_model=list[str])
def list_tags(
    query: str
    | None = Query(None, alias="q", description="Filter tags using this substring"),
    limit: int = Query(50, ge=1, le=200, description="Max number of tags to return"),
    user: UserRead = Depends(get_current_user),
    db_history: GraphHistoryRelationalInterface = Depends(get_graph_history_db),
):
    if not can_read(user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You must be logged in to view tags",
        )
    return db_history.list_tags(query=query, limit=limit)

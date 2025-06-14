from fastapi import Depends, APIRouter

from backend.db.base import GraphHistoryRelationalInterface
from backend.db.connections import get_graph_history_db
from backend.dynamic_models import DynamicEdge
from backend.models import NodeId


router = APIRouter(prefix="/edges", tags=["edges"])


@router.get("")
def get_edge_list(
    db_history: GraphHistoryRelationalInterface = Depends(
        get_graph_history_db
    ),
) -> list[DynamicEdge]: #type: ignore
    """Return all edges in the database."""
    return db_history.get_edge_list()


@router.post("/find")
def find_edges(
    source_id: NodeId = None,
    target_id: NodeId = None,
    edge_type: str = None,
    db_history: GraphHistoryRelationalInterface = Depends(
        get_graph_history_db
    ),
) -> list[DynamicEdge]: #type: ignore
    """Return the edge associated with the provided ID."""
    return db_history.find_edges(
        source_id=source_id, target_id=target_id, edge_type=edge_type
    )
from fastapi import Body, Depends, APIRouter, HTTPException

from backend.api.auth import get_current_user
from backend.db.base import GraphDatabaseInterface, GraphHistoryRelationalInterface
from backend.db.connections import get_graph_db, get_graph_history_db
from backend.dynamic_models import DynamicEdge, EdgeTypeModels
from backend.models import GraphHistoryEvent, NodeId, UserRead


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


@router.get("/{source_id}/{target_id}")
def get_edge(
    source_id: NodeId,
    target_id: NodeId,
    db_history: GraphHistoryRelationalInterface = Depends(
        get_graph_history_db
    ),
) -> DynamicEdge: #type: ignore
    """Return the edge associated with the provided ID."""
    return db_history.get_edge(source_id, target_id)


@router.post("", status_code=201)
def create_edge(
    payload: dict = Body(...),
    db_graph: GraphDatabaseInterface | None = Depends(get_graph_db),
    db_history: GraphHistoryRelationalInterface = Depends(
        get_graph_history_db
    ),
    user: UserRead = Depends(get_current_user),
) -> DynamicEdge: #type: ignore
    """Create an edge."""
    et = payload.get("edge_type")
    Model = EdgeTypeModels.get(et)
    if not Model:
        raise HTTPException(400, f"Unknown edge_type {et!r}")
    edge = Model(**payload)
    out_edge = db_history.create_edge(edge, username=user.username)
    if db_graph is not None:
        db_graph.create_edge(edge)
    return out_edge


@router.delete("/{source_id}/{target_id}")
def delete_edge(
    source_id: NodeId,
    target_id: NodeId,
    edge_type: str | None = None,
    db_graph: GraphDatabaseInterface | None = Depends(get_graph_db),
    db_history: GraphHistoryRelationalInterface = Depends(
        get_graph_history_db
    ),
    user: UserRead = Depends(get_current_user),
):
    """Delete the edge between two nodes and for an optional edge_type."""
    db_history.delete_edge(source_id, target_id, edge_type, username=user.username)
    if db_graph is not None:
        db_graph.delete_edge(source_id, target_id, edge_type)


@router.put("")
def update_edge(
    payload: dict = Body(...),
    db_graph: GraphDatabaseInterface | None = Depends(get_graph_db),
    db_history: GraphHistoryRelationalInterface = Depends(
        get_graph_history_db
    ),
    user: UserRead = Depends(get_current_user),
) -> DynamicEdge: #type: ignore
    """Update the properties of an edge."""
    et = payload.get("edge_type")
    Model = EdgeTypeModels.get(et)
    if not Model:
        raise HTTPException(400, f"Unknown edge_type {et!r}")
    edge = Model(**payload)
    out_edge = db_history.update_edge(edge, username=user.username)
    if db_graph is not None:
        db_graph.update_edge(edge)
    return out_edge


@router.get("/{source_id}/{target_id}/history")
def get_edge_history(
    source_id: NodeId,
    target_id: NodeId,
    db_history: GraphHistoryRelationalInterface = Depends(
        get_graph_history_db
    ),
) -> list[GraphHistoryEvent]:
    """Return the history of the edge associated with the provided source and target IDs."""
    return db_history.get_edge_history(source_id, target_id)
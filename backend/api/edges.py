import logging
import datetime

from fastapi import Body, Depends, APIRouter, HTTPException, Query, status, Path

from backend.api.auth import get_current_user
from backend.utils.permissions import (
    can_read,
    can_create,
    can_edit,
    can_delete,
    can_rate,
)
from backend.db.base import (
    GraphDatabaseInterface,
    GraphHistoryRelationalInterface,
    RatingHistoryRelationalInterface,
)
from backend.db.connections import (
    get_graph_db,
    get_graph_history_db,
    get_rating_history_db,
)
from backend.models.dynamic import DynamicEdge, EdgeTypeModels
from backend.models.fixed import (
    GraphHistoryEvent,
    NodeId,
    RatingEvent,
    UserRead,
    EntityType,
)


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/edges", tags=["edges"])


# **** ratings for batch of edges ****


@router.get(
    "/ratings",
    summary="Batch: list ratings for multiple edges",
    response_model=dict[str, list[RatingEvent]],
)
def get_edges_ratings(
    edge_ids: list[str] = Query(..., description="List of 'src-tgt' edge IDs"),
    poll_label: str = Query(..., description="Label of the poll to filter ratings"),
    user: UserRead = Depends(get_current_user),
    db: RatingHistoryRelationalInterface = Depends(get_rating_history_db),
) -> dict[str, list[RatingEvent]]:
    # Check read permissions
    if not can_read(user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You must be logged in to view content",
        )

    pairs = [(int(s), int(t)) for s, t in (e.split("-") for e in edge_ids)]
    raw = db.get_edges_ratings(pairs, poll_label)
    return {f"{s}-{t}": evs for (s, t), evs in raw.items()}


@router.get("/ratings/median")
def get_edges_median_ratings(
    edge_ids: list[str] = Query(
        ..., description="List of edges in form 'source-target'"  # no alias
    ),
    poll_label: str
    | None = Query(None, description="Label of the poll to filter ratings"),
    user: UserRead = Depends(get_current_user),
    db: RatingHistoryRelationalInterface = Depends(get_rating_history_db),
) -> dict[str, dict | None]:
    """
    Retrieve the median ratings for multiple edges.
    Returns a mapping: { "source-target": {"median_rating": <value>} }.
    If an edge doesn't have ratings, the value will be None.
    """
    # Check read permissions
    if not can_read(user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You must be logged in to view content",
        )

    start_time = datetime.datetime.now()
    # Convert string keys to a list of (source_id, target_id) for the DB method
    edges = []
    for key in edge_ids:
        src_str, tgt_str = key.split("-")
        edges.append((int(src_str), int(tgt_str)))

    medians = db.get_edges_median_ratings(edges, poll_label)
    duration = datetime.datetime.now() - start_time
    logger.info(
        f"Retrieved median ratings for {len(edge_ids)} edges in {duration.total_seconds() * 1000:.2f}ms"
    )

    return {
        key: {
            "median_rating": (
                medians[(int(src), int(tgt))].value
                if medians[(int(src), int(tgt))]
                else None
            )
        }
        for key in edge_ids
        for src, tgt in [key.split("-")]
    }


# **** Edge CRUD operations ****


@router.get("")
def get_edges(
    node_ids: list[NodeId] = Query(
        None, description="Optional list of node IDs to filter connections"
    ),
    user: UserRead = Depends(get_current_user),
    db_history: GraphHistoryRelationalInterface = Depends(get_graph_history_db),
) -> list[DynamicEdge]:
    """Return edges, optionally filtered by node connections."""
    # Check read permissions
    if not can_read(user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You must be logged in to view content",
        )

    full_edge_list = db_history.get_edge_list()
    if node_ids:
        edge_list = []
        # Get connections between the specified nodes
        for edge in full_edge_list:
            if edge.source in node_ids and edge.target in node_ids:
                edge_list += [edge]
        return edge_list
    return full_edge_list


@router.post("", status_code=201)
def create_edge(
    payload: dict = Body(...),
    db_graph: GraphDatabaseInterface | None = Depends(get_graph_db),
    db_history: GraphHistoryRelationalInterface = Depends(get_graph_history_db),
    user: UserRead = Depends(get_current_user),
) -> DynamicEdge:  # type: ignore
    """Create an edge."""
    # Check permissions
    if not can_create(user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to create edges",
        )

    et = payload.get("edge_type")
    Model = EdgeTypeModels.get(et)
    if not Model:
        raise HTTPException(400, f"Unknown edge_type {et!r}")
    # TODO: validate payload further, within graph, against Graph Schema
    edge = Model(**payload)
    out_edge = db_history.create_edge(edge, username=user.username)
    if db_graph is not None:
        db_graph.create_edge(edge)
    return out_edge


@router.put("")
def update_edge(
    payload: dict = Body(...),
    db_graph: GraphDatabaseInterface | None = Depends(get_graph_db),
    db_history: GraphHistoryRelationalInterface = Depends(get_graph_history_db),
    user: UserRead = Depends(get_current_user),
) -> DynamicEdge:  # type: ignore
    """Update the properties of an edge."""
    # Check permissions
    if not can_edit(user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to edit edges",
        )

    et = payload.get("edge_type")
    Model = EdgeTypeModels.get(et)
    if not Model:
        raise HTTPException(400, f"Unknown edge_type {et!r}")
    # TODO: validate payload further, within graph, against Graph Schema
    edge = Model(**payload)
    out_edge = db_history.update_edge(edge, username=user.username)
    if db_graph is not None:
        db_graph.update_edge(edge)
    return out_edge


@router.post("/find")
def find_edges(
    source_id: NodeId = None,
    target_id: NodeId = None,
    edge_type: str = None,
    user: UserRead = Depends(get_current_user),
    db_history: GraphHistoryRelationalInterface = Depends(get_graph_history_db),
) -> list[DynamicEdge]:  # type: ignore
    """Return the edge associated with the provided ID."""
    # Check read permissions
    if not can_read(user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You must be logged in to view content",
        )

    return db_history.find_edges(
        source_id=source_id, target_id=target_id, edge_type=edge_type
    )


@router.get("/{source_id}/{target_id}")
def get_edge(
    source_id: NodeId,
    target_id: NodeId,
    user: UserRead = Depends(get_current_user),
    db_history: GraphHistoryRelationalInterface = Depends(get_graph_history_db),
) -> DynamicEdge:  # type: ignore
    """Return the edge associated with the provided ID."""
    # Check read permissions
    if not can_read(user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You must be logged in to view content",
        )

    return db_history.get_edge(source_id, target_id)


@router.delete("/{source_id}/{target_id}")
def delete_edge(
    source_id: NodeId,
    target_id: NodeId,
    edge_type: str | None = None,
    db_graph: GraphDatabaseInterface | None = Depends(get_graph_db),
    db_history: GraphHistoryRelationalInterface = Depends(get_graph_history_db),
    user: UserRead = Depends(get_current_user),
):
    """Delete the edge between two nodes and for an optional edge_type."""
    # Check permissions
    if not can_delete(user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to delete edges",
        )

    db_history.delete_edge(source_id, target_id, edge_type, username=user.username)
    if db_graph is not None:
        db_graph.delete_edge(source_id, target_id, edge_type)


@router.get("/{source_id}/{target_id}/history")
def get_edge_history(
    source_id: NodeId,
    target_id: NodeId,
    user: UserRead = Depends(get_current_user),
    db_history: GraphHistoryRelationalInterface = Depends(get_graph_history_db),
) -> list[GraphHistoryEvent]:
    """Return the history of the edge associated with the provided source and target IDs."""
    # Check read permissions
    if not can_read(user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You must be logged in to view content",
        )

    return db_history.get_edge_history(source_id, target_id)


# ****  per-edge ratings ****

ratings_router = APIRouter(
    prefix="/{source_id}/{target_id}/ratings",
    tags=["ratings"],
    responses={404: {"description": "Not found"}},
)


@ratings_router.post(
    "", status_code=status.HTTP_201_CREATED, response_model=RatingEvent
)
def log_edge_rating(
    source_id: int = Path(...),
    target_id: int = Path(...),
    rating: RatingEvent = Body(...),
    user: UserRead = Depends(get_current_user),
    db: RatingHistoryRelationalInterface = Depends(get_rating_history_db),
) -> RatingEvent:
    # Check permissions
    if not can_rate(user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to rate edges",
        )

    rating.entity_type = EntityType.edge
    rating.username = user.username
    rating.source_id = source_id
    rating.target_id = target_id
    return db.log_rating(rating)


@ratings_router.get("/me")  # /rating/edge/{source_id}/{target_id}
def get_edge_rating(
    source_id: int,
    target_id: int,
    poll_label: str,
    db: RatingHistoryRelationalInterface = Depends(get_rating_history_db),
    user: UserRead = Depends(get_current_user),
) -> RatingEvent | None:
    """
    Retrieve a user's rating for an edge.
    """
    return db.get_edge_rating(source_id, target_id, poll_label, user.username)


@ratings_router.get("/median")
def get_edge_median_rating(
    source_id: int,
    target_id: int,
    poll_label: str,
    user: UserRead = Depends(get_current_user),
    db: RatingHistoryRelationalInterface = Depends(get_rating_history_db),
) -> dict | None:
    """
    Retrieve the median rating for a given edge.
    """
    # Check read permissions
    if not can_read(user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You must be logged in to view content",
        )

    logger.warning("Function may not be working as expected")
    median = db.get_edge_median_rating(source_id, target_id, poll_label)
    return {"median_rating": median}


@ratings_router.get("")
def get_edge_ratings(
    source_id: int,
    target_id: int,
    poll_label: str
    | None = Query(None, description="Optional poll label to filter ratings"),
    user: UserRead = Depends(get_current_user),
    db: RatingHistoryRelationalInterface = Depends(get_rating_history_db),
) -> dict:
    """
    Retrieve all ratings for a given edge.
    """
    # Check read permissions
    if not can_read(user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You must be logged in to view content",
        )

    ratings = db.get_edge_ratings(source_id, target_id, poll_label)
    # Convert each RatingEvent to dict.
    return {"ratings": ratings}


router.include_router(ratings_router)

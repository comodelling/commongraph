import logging
import datetime

from fastapi import Body, Depends, HTTPException, Query, APIRouter, status, Path
from sqlmodel import Session

from backend.api.auth import get_current_user
from backend.utils.permissions import can_read, can_create, can_edit, can_delete, can_rate
from backend.db.base import GraphDatabaseInterface, GraphHistoryRelationalInterface, RatingHistoryRelationalInterface
from backend.db.connections import get_graph_db, get_graph_history_db, get_rating_history_db, get_relational_session
from backend.db.janusgraph import JanusGraphDB
from backend.models.fixed import GraphHistoryEvent, NodeId, RatingEvent, UserRead, EntityType
from backend.models.dynamic import DynamicNode, NodeTypeModels, NodeSearchResult
from backend.properties import NodeStatus
from backend.api.scopes import get_or_create_scope

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/nodes", tags=["nodes"])



@router.get("", response_model=list[NodeSearchResult])
def search_nodes(
    node_type: list[str] | str = Query(None),
    title: str | None = None,
    scope: str | None = None,
    status: list[NodeStatus] | NodeStatus = Query(None),
    tags: list[str] | None = Query(None),
    rating: float | None = None,
    description: str | None = None,
    user: UserRead = Depends(get_current_user),
    db_graph: GraphDatabaseInterface | None = Depends(get_graph_db),
    db_history: GraphHistoryRelationalInterface = Depends(
        get_graph_history_db
    ),
    db_ratings: RatingHistoryRelationalInterface = Depends(
        get_rating_history_db
    ),
):
    """Search in nodes on a field by field level."""
    # Check read permissions
    if not can_read(user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You must be logged in to view content"
        )
    
    if db_graph is not None:
        nodes = db_graph.search_nodes(
            node_type=node_type,
            title=title,
            scope=scope,
            status=status,
            tags=tags,
            description=description,
        )
    else:
        nodes = db_history.search_nodes(
            node_type=node_type,
            title=title,
            scope=scope,
            status=status,
            tags=tags,
            description=description,
        )
    out: list[NodeSearchResult] = []
    for node in nodes:
        # grab last event timestamp
        history = db_history.get_node_history(node.node_id)
        last_ts = history[-1].timestamp if history else datetime.datetime.now(datetime.timezone.utc)
        # merge node → NodeSearchResult
        payload = node.model_dump()
        payload["last_modified"] = last_ts
        out.append(NodeSearchResult(**payload))
    
    if rating is None:
        return out
    else:
        raise HTTPException(
            status_code=400,
            detail="Search by rating is not supported currently. "
        )
        # nodes_ids = [el.node_id for el in nodes]
        # medians = db_ratings.get_nodes_median_ratings(nodes_ids, RatingType.support)
        # return [node for node in nodes if medians[node.node_id] == rating]


@router.get("/random")
def get_random_node(
    node_type: str | None = None,
    user: UserRead = Depends(get_current_user),
    db: GraphDatabaseInterface | None = Depends(get_graph_db),
    db_history: GraphHistoryRelationalInterface = Depends(
        get_graph_history_db
    ),
) -> DynamicNode: #type: ignore
    """Return a random node with optional node_type."""
    # Check read permissions
    if not can_read(user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You must be logged in to view content"
        )
    
    if isinstance(db, JanusGraphDB):
        return db.get_random_node(node_type)
    return db_history.get_random_node(node_type)


@router.get("/{node_id}")
def get_node(
    node_id: NodeId,
    user: UserRead = Depends(get_current_user),
    db_history: GraphHistoryRelationalInterface = Depends(
        get_graph_history_db
    ),
) -> DynamicNode: #type: ignore
    """Return the node associated with the provided ID."""
    # Check read permissions
    if not can_read(user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You must be logged in to view content"
        )
    
    return db_history.get_node(node_id)


@router.post("", status_code=status.HTTP_201_CREATED)
def create_node(
    payload: dict = Body(...),
    db_graph: GraphDatabaseInterface | None = Depends(get_graph_db),
    db_history: GraphHistoryRelationalInterface = Depends(
        get_graph_history_db
    ),
    session: Session = Depends(get_relational_session),
    user: UserRead = Depends(get_current_user),
) -> DynamicNode: #type: ignore
    """Create a node."""
    # Check permissions
    if not can_create(user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to create nodes"
        )
    
    nt = payload.get("node_type")
    Model = NodeTypeModels.get(nt)
    if not Model:
        raise HTTPException(400, f"Unknown node_type {nt!r}")
    
    # Handle scope: ensure it exists in the scopes table
    if "scope" in payload and payload["scope"]:
        try:
            get_or_create_scope(payload["scope"], session)
            session.commit()  # Commit the scope creation
        except Exception as e:
            logger.error(f"Failed to create scope: {e}")
            session.rollback()
            raise HTTPException(500, f"Failed to create scope: {str(e)}")
    
    #TODO: validate payload further, within graph, against Graph Schema
    node = Model(**payload)

    if db_graph is not None:
        node = db_graph.create_node(node)
        # logger.info(f"User {user.username} created node {node_out.node_id} in graph database too")

    node_out = db_history.create_node(
        node, username=user.username
    )  # reuse the ID allocated from the graph database
    return node_out


@router.delete("/{node_id}")
def delete_node(
    node_id: NodeId,
    db_graph: GraphDatabaseInterface | None = Depends(get_graph_db),
    db_history: GraphHistoryRelationalInterface = Depends(
        get_graph_history_db
    ),
    user: UserRead = Depends(get_current_user),
):
    """Delete the node with provided ID."""
    # Check permissions
    if not can_delete(user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to delete nodes"
        )
    
    db_history.delete_node(node_id, username=user.username)
    if db_graph is not None:
        db_graph.delete_node(node_id)


@router.put("")
def update_node(
    payload: dict = Body(...),
    db_graph: GraphDatabaseInterface | None = Depends(get_graph_db),
    db_history: GraphHistoryRelationalInterface = Depends(
        get_graph_history_db
    ),
    session: Session = Depends(get_relational_session),
    user: UserRead = Depends(get_current_user),
) -> DynamicNode: #type: ignore
    """Update the properties of an existing node."""
    # Check permissions
    if not can_edit(user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to edit nodes"
        )
    
    nt = payload.get("node_type")
    Model = NodeTypeModels.get(nt)
    if not Model:
        raise HTTPException(400, f"Unknown node_type {nt!r}")
    
    # Handle scope: ensure it exists in the scopes table
    if "scope" in payload and payload["scope"]:
        try:
            get_or_create_scope(payload["scope"], session)
            session.commit()  # Commit the scope creation
        except Exception as e:
            logger.error(f"Failed to create scope: {e}")
            session.rollback()
            raise HTTPException(500, f"Failed to create scope: {str(e)}")
    
    #TODO: validate payload further, within graph, against Graph Schema
    node = Model(**payload)
    node_out = db_history.update_node(node, username=user.username)
    if db_graph is not None:
        db_graph.update_node(node)
    return node_out


@router.get("/{node_id}/history")
def get_node_history(
    node_id: NodeId,
    user: UserRead = Depends(get_current_user),
    db_history: GraphHistoryRelationalInterface = Depends(
        get_graph_history_db
    ),
) -> list[GraphHistoryEvent]:
    """Return the history of the node associated with the provided ID."""
    # Check read permissions
    if not can_read(user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You must be logged in to view content"
        )
    
    return db_history.get_node_history(node_id)


# **** ratings for batches of nodes ****


@router.get("/ratings/median")
def get_nodes_median_ratings(
  node_ids: list[NodeId] = Query(...),
  poll_label: str | None = Query(
    None, description="Optional poll_label; if omitted, return all"
  ),
  user: UserRead = Depends(get_current_user),
  db: RatingHistoryRelationalInterface = Depends(get_rating_history_db),
):
    # Check read permissions
    if not can_read(user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You must be logged in to view content"
        )
    
    # default = all polls in your config
    from backend.config import POLLS_CFG
    labels = [poll_label] if poll_label else list(POLLS_CFG.keys())

    # for each poll, get a map node_id → median
    per_poll = {
      pl: db.get_nodes_median_ratings(node_ids, pl)
      for pl in labels
    }

    # invert into node-centric structure
    out: dict[int, dict[str, float|None]] = {
      nid: {pl: per_poll[pl].get(nid) for pl in labels}
      for nid in node_ids
    }
    return out


@router.get(
    "/ratings", 
    response_model=dict[int, list[RatingEvent]],
    summary="Batch: list ratings for multiple nodes",
)
def get_nodes_ratings(
    node_ids: list[NodeId] = Query(..., description="List of node IDs"),
    poll_label: str = Query(
        ..., description="Optional poll label to filter ratings"
    ),
    user: UserRead = Depends(get_current_user),
    db: RatingHistoryRelationalInterface = Depends(get_rating_history_db),
) -> dict[int, list[RatingEvent]]:
    # Check read permissions
    if not can_read(user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You must be logged in to view content"
        )
    
    return db.get_nodes_ratings(node_ids, poll_label)


# **** per-node ratings ****

ratings_router = APIRouter(
    prefix="/{node_id}/ratings", 
    tags=["ratings"], 
    responses={404: {"description": "Not found"}},
)


@ratings_router.post(
    "", status_code=status.HTTP_201_CREATED, response_model=RatingEvent
)
def log_node_rating(
    node_id: int = Path(..., description="ID of the node"),
    rating: RatingEvent = Body(...),
    user: UserRead = Depends(get_current_user),
    db: RatingHistoryRelationalInterface = Depends(get_rating_history_db),
) -> RatingEvent:
    # Check permissions
    if not can_rate(user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to rate nodes"
        )
    
    evt = RatingEvent(
      username=user.username,
      entity_type=EntityType.node,
      node_id=node_id,
      poll_label=rating.poll_label,
      rating=rating.rating
    )
    return db.log_rating(evt)


@ratings_router.get(
    "/me", 
    response_model= RatingEvent | None,
    summary="Get my rating for one node",
)
def get_my_node_rating(
    node_id: int,
    poll_label: str = Query(..., description="Label of the poll to filter ratings"),
    user: UserRead = Depends(get_current_user),
    db: RatingHistoryRelationalInterface = Depends(get_rating_history_db),
) -> RatingEvent | None:
    return db.get_node_rating(node_id, poll_label, user.username)


@ratings_router.get(
    "/median", 
    summary="Get median rating for one node",
)
def get_node_median_rating(
    node_id: int,
    poll_label: str = Query(..., description="Label of the poll to filter ratings"),
    user: UserRead = Depends(get_current_user),
    db: RatingHistoryRelationalInterface = Depends(get_rating_history_db),
) -> dict | None:
    """
    Retrieve the median rating for a given node.
    """
    # Check read permissions
    if not can_read(user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You must be logged in to view content"
        )
    
    median = db.get_node_median_rating(node_id, poll_label)
    return {"median_rating": median}


@ratings_router.get("",
                    summary="List all ratings for one node")
def get_node_ratings(
    node_id: int,
    poll_label: str = Query(..., description="Label of the poll to filter ratings"),
    user: UserRead = Depends(get_current_user),
    db: RatingHistoryRelationalInterface = Depends(get_rating_history_db),
) -> dict:
    """
    Retrieve all ratings for a given node.
    """
    # Check read permissions
    if not can_read(user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You must be logged in to view content"
        )
    
    ratings = db.get_node_ratings(node_id, poll_label)
    # Convert each RatingEvent to dict.
    return {"ratings": ratings}


router.include_router(ratings_router)

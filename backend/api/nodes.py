from fastapi import Body, Depends, HTTPException, Query, APIRouter, status

from backend.api.auth import get_current_user
from backend.db.base import GraphDatabaseInterface, GraphHistoryRelationalInterface, RatingHistoryRelationalInterface
from backend.db.connections import get_graph_db, get_graph_history_db, get_rating_history_db
from backend.db.janusgraph import JanusGraphDB
from backend.dynamic_models import DynamicNode, NodeTypeModels
from backend.models import GraphHistoryEvent, LikertScale, NodeId, RatingType, UserRead
from backend.properties import NodeStatus


router = APIRouter(prefix="/nodes", tags=["nodes"])


@router.get("")
def search_nodes(
    node_type: list[str] | str = Query(None),
    title: str | None = None,
    scope: str | None = None,
    status: list[NodeStatus] | NodeStatus = Query(None),
    tags: list[str] | None = Query(None),
    rating: LikertScale | None = None,
    description: str | None = None,
    db_graph: GraphDatabaseInterface | None = Depends(get_graph_db),
    db_history: GraphHistoryRelationalInterface = Depends(
        get_graph_history_db
    ),
    db_ratings: RatingHistoryRelationalInterface = Depends(
        get_rating_history_db
    ),
) -> list[DynamicNode]: #type: ignore
    """Search in nodes on a field by field level."""
    if db_graph is not None:
        nodes = db_graph.search_nodes(
            node_type=node_type,
            title=title,
            scope=scope,
            status=status,
            tags=tags,
            description=description,
        )
    nodes = db_history.search_nodes(
        node_type=node_type,
        title=title,
        scope=scope,
        status=status,
        tags=tags,
        description=description,
    )
    if rating is None:
        return nodes
    else:
        nodes_ids = [el.node_id for el in nodes]
        medians = db_ratings.get_nodes_median_ratings(nodes_ids, RatingType.support)
        return [node for node in nodes if medians[node.node_id] == rating]


@router.get("/random")
def get_random_node(
    node_type: str | None = None,
    db: GraphDatabaseInterface | None = Depends(get_graph_db),
    db_history: GraphHistoryRelationalInterface = Depends(
        get_graph_history_db
    ),
) -> DynamicNode: #type: ignore
    """Return a random node with optional node_type."""
    if isinstance(db, JanusGraphDB):
        return db.get_random_node(node_type)
    return db_history.get_random_node(node_type)


@router.get("/{node_id}")
def get_node(
    node_id: NodeId,
    db_history: GraphHistoryRelationalInterface = Depends(
        get_graph_history_db
    ),
) -> DynamicNode: #type: ignore
    """Return the node associated with the provided ID."""
    return db_history.get_node(node_id)


@router.post("", status_code=status.HTTP_201_CREATED)
def create_node(
    payload: dict = Body(...),
    db_graph: GraphDatabaseInterface | None = Depends(get_graph_db),
    db_history: GraphHistoryRelationalInterface = Depends(
        get_graph_history_db
    ),
    user: UserRead = Depends(get_current_user),
) -> DynamicNode: #type: ignore
    """Create a node."""
    nt = payload.get("node_type")
    Model = NodeTypeModels.get(nt)
    if not Model:
        raise HTTPException(400, f"Unknown node_type {nt!r}")
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
    user: UserRead = Depends(get_current_user),
) -> DynamicNode: #type: ignore
    """Update the properties of an existing node."""
    nt = payload.get("node_type")
    Model = NodeTypeModels.get(nt)
    if not Model:
        raise HTTPException(400, f"Unknown node_type {nt!r}")
    node = Model(**payload)
    node_out = db_history.update_node(node, username=user.username)
    if db_graph is not None:
        db_graph.update_node(node)
    return node_out


@router.get("/{node_id}/history")
def get_node_history(
    node_id: NodeId,
    db_history: GraphHistoryRelationalInterface = Depends(
        get_graph_history_db
    ),
) -> list[GraphHistoryEvent]:
    """Return the history of the node associated with the provided ID."""
    return db_history.get_node_history(node_id)
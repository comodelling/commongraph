from fastapi import Depends, Query, APIRouter

from backend.db.base import GraphDatabaseInterface, GraphHistoryRelationalInterface, RatingHistoryRelationalInterface
from backend.db.connections import get_graph_db, get_graph_history_db, get_rating_history_db
from backend.dynamic_models import DynamicNode
from backend.models import LikertScale, RatingType
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
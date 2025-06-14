import datetime
from typing import Annotated
import logging

from fastapi import Depends, Query, status, APIRouter

from backend.api.auth import get_current_user
from backend.config import EDGE_TYPE_BETWEEN, EDGE_TYPE_PROPS, NODE_TYPE_PROPS
from backend.db.base import GraphDatabaseInterface, GraphHistoryRelationalInterface
from backend.db.connections import get_graph_db, get_graph_history_db
from backend.dynamic_models import DynamicGraphExport, DynamicSubgraph
from backend.models import NodeId, UserRead
from backend.version import __version__

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/graph", tags=["graph"])


@router.get("")
def get_whole_graph(
    db_history: GraphHistoryRelationalInterface = Depends(
        get_graph_history_db
    ),
) -> DynamicGraphExport:
    """Return full graph of nodes and edges from the database."""
    out = db_history.get_whole_graph().model_dump()
    out["commongraph_version"] = __version__
    out["timestamp"] = datetime.datetime.now().isoformat()
    return out


@router.put("")
def update_subgraph(
    subgraph: DynamicSubgraph,
    db_graph: GraphDatabaseInterface | None = Depends(get_graph_db),
    db_history: GraphHistoryRelationalInterface = Depends(
        get_graph_history_db
    ),
    user: UserRead = Depends(get_current_user),
)  -> DynamicSubgraph:
    """Add missing nodes and edges and update existing ones (given IDs)."""
    out_subgraph = db_history.update_graph(subgraph, username=user.username)
    if db_graph is not None:
        db_graph.update_graph(subgraph)
    return out_subgraph


@router.delete("", status_code=status.HTTP_205_RESET_CONTENT)
def reset_whole_graph(
    db_graph: GraphDatabaseInterface | None = Depends(get_graph_db),
    db_history: GraphHistoryRelationalInterface = Depends(
        get_graph_history_db
    ),
    user: UserRead = Depends(get_current_user),
) -> None:
    """Delete all nodes and edges. Be careful!"""
    db_history.reset_whole_graph(username=user.username)
    if db_graph is not None:
        db_graph.reset_whole_graph()


@router.get("/summary")
def get_graph_summary(
    db_history: GraphHistoryRelationalInterface = Depends(
        get_graph_history_db
    ),
) -> dict[str, int]:
    """Count nodes and edges."""
    return db_history.get_graph_summary()


@router.get("/schema")
def get_schema():
    """Return the schema of the graph database, as a graph."""
    edge_types = []
    for edge_type in EDGE_TYPE_PROPS.keys():
        if edge_type in EDGE_TYPE_BETWEEN and EDGE_TYPE_BETWEEN[edge_type] is not None:
            logger.info(f"EDGE_TYPE_BETWEEN: {EDGE_TYPE_BETWEEN}")
            for node_type1, node_type2 in EDGE_TYPE_BETWEEN[edge_type]:
                if node_type1 == node_type2:
                    #TODO: check this in config read
                    continue
                edge_types += [
                    {
                        "source_type": node_type1,
                        "target_type": node_type2,
                        "label": edge_type,
                    }
                ]
        else:
            for node_type1 in NODE_TYPE_PROPS.keys():
                for node_type2 in NODE_TYPE_PROPS.keys():
                    if node_type1 == node_type2:
                        continue
                    edge_types += [
                        {
                            "source_type": node_type1,
                            "target_type": node_type2,
                            "label": edge_type,
                        }
                    ]
    return {
        "node_types": list(NODE_TYPE_PROPS.keys()),
        "edge_types": edge_types,
    }


# needs to be placed after /schema and /summary
@router.get("/{node_id}")
def get_induced_subgraph(
    node_id: NodeId,
    levels: Annotated[int, Query(get=0)] = 2,
    db_graph: GraphDatabaseInterface | None = Depends(get_graph_db),
    db_history: GraphHistoryRelationalInterface = Depends(
        get_graph_history_db
    ),
) -> DynamicSubgraph:
    """Return the subgraph induced from a particular element with an optional limit number of connections.
    If no neighbour is found, a singleton subgraph with a single node is returned from the provided ID.
    """
    if db_graph is not None:
        return db_graph.get_induced_subgraph(node_id, levels)
    return db_history.get_induced_subgraph(node_id, levels)



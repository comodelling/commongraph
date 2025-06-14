import datetime

from fastapi import Depends, status, APIRouter

from backend.api.auth import get_current_user
from backend.db.base import GraphDatabaseInterface, GraphHistoryRelationalInterface
from backend.db.connections import get_graph_db, get_graph_history_db
from backend.dynamic_models import DynamicNetworkExport
from backend.models import UserRead
from backend.version import __version__


router = APIRouter(prefix="/graph", tags=["graph"])


@router.get("")
def get_whole_graph(
    db_history: GraphHistoryRelationalInterface = Depends(
        get_graph_history_db
    ),
) -> DynamicNetworkExport:
    """Return full network of nodes and edges from the database."""
    out = db_history.get_whole_network().model_dump()
    out["commongraph_version"] = __version__
    out["timestamp"] = datetime.datetime.now().isoformat()
    return out


@router.get("/summary")
def get_graph_summary(
    db_history: GraphHistoryRelationalInterface = Depends(
        get_graph_history_db
    ),
) -> dict[str, int]:
    """Count nodes and edges."""
    return db_history.get_network_summary()


@router.delete("", status_code=status.HTTP_205_RESET_CONTENT)
def reset_whole_graph(
    db_graph: GraphDatabaseInterface | None = Depends(get_graph_db),
    db_history: GraphHistoryRelationalInterface = Depends(
        get_graph_history_db
    ),
    user: UserRead = Depends(get_current_user),
) -> None:
    """Delete all nodes and edges. Be careful!"""
    db_history.reset_whole_network(username=user.username)
    if db_graph is not None:
        db_graph.reset_whole_network()
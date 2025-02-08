import os
import warnings
from pathlib import Path as PathlibPath
from typing import Annotated
import logging

from dotenv import load_dotenv
from fastapi import FastAPI, status, Query, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from models import (
    NodeBase,
    EdgeBase,
    Subnet,
    NodeType,
    NodeStatus,
    NodeId,
    EdgeType,
    PartialNodeBase,
    MigrateLabelRequest,
    User,
    UserRead,
    GraphHistoryEvent,
    OperationType,
)
from database.base import (
    GraphDatabaseInterface,
    UserDatabaseInterface,
    GraphHistoryDatabaseInterface,
)
from database.janusgraph import JanusGraphDB
from database.sqlite import SQLiteDB
from database.postgresql import UserPostgreSQLDB, GraphHistoryPostgreSQLDB
from auth import router as auth_router
from auth import get_current_user

logger = logging.getLogger(__name__)

if os.getenv("DOCKER_ENV"):
    _version_path = PathlibPath("/app/VERSION")
    _env_path = PathlibPath("/app/backend/.env")
elif os.getcwd().endswith("backend"):
    _version_path = PathlibPath("../VERSION")
    _env_path = PathlibPath(".env")
elif os.getcwd().endswith("objectivenet"):
    _version_path = PathlibPath("VERSION")
    _env_path = PathlibPath("backend/.env")
else:
    raise FileNotFoundError("VERSION file not found")
with open(_version_path) as f:
    __version__ = f.read().strip()

if _env_path.exists():
    load_dotenv(dotenv_path=_env_path)
else:
    warnings.warn(
        f".env file not found at {_env_path}, using default environment variables"
    )

origins = (
    [origin.strip() for origin in os.getenv("ALLOWED_ORIGINS", "").split(",")]
    if os.getenv("ALLOWED_ORIGINS")
    else []
)


app = FastAPI(title="ObjectiveNet API", version=__version__)
app.include_router(auth_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_graph_db_connection(
    db_type: str = os.getenv("GRAPH_DB_TYPE"),
) -> GraphDatabaseInterface:
    if db_type == "janusgraph":
        janusgraph_host = os.getenv("JANUSGRAPH_HOST", "localhost")
        traversal_source = os.getenv("TRAVERSAL_SOURCE", "g_test")
        return JanusGraphDB(janusgraph_host, traversal_source)
    elif db_type == "sqlite":
        db_path = os.getenv("SQLITE_DB_PATH", "objectivenet-db.sqlite3")
        print(f"Using SQLite database at {db_path}")
        return SQLiteDB(db_path)
    else:
        raise ValueError(f"Unsupported GRAPH_DB_TYPE: {db_type}")


def get_user_db_connection(
    db_type: str = os.getenv("RELATIONAL_DB_TYPE"),
) -> UserDatabaseInterface:
    if db_type == "postgresql":
        database_url = os.getenv("POSTGRES_DB_URL")
        print(f"Using User PostgreSQL database at {database_url}")
        return UserPostgreSQLDB(database_url)
    else:
        raise ValueError(f"Unsupported RELATIONAL_DB_TYPE: {db_type}")


def get_graph_history_db_connection(
    db_type: str = os.getenv("RELATIONAL_DB_TYPE"),
) -> GraphHistoryDatabaseInterface:
    if db_type == "postgresql":
        database_url = os.getenv("POSTGRES_DB_URL")
        print(f"Using Graph History PostgreSQL database at {database_url}")
        return GraphHistoryPostgreSQLDB(database_url)
    else:
        raise ValueError(f"Unsupported RELATIONAL_DB_TYPE: {db_type}")


### root ###


@app.get("/")
async def root():
    return {"message": "Welcome to ObjectiveNet!"}


### /user/ ###


@app.post("/users", status_code=201)
def create_user(
    user: User, db: UserDatabaseInterface = Depends(get_user_db_connection)
) -> User:
    """Create a new user."""
    return db.create_user(user)


@app.get("/users/{username}")
def get_user(
    username: str, db: UserDatabaseInterface = Depends(get_user_db_connection)
) -> User:
    """Get a user by username."""
    user = db.get_user(username)
    if user:
        return user
    raise HTTPException(status_code=404, detail="User not found")


### /network/ ###


@app.get("/network")
def get_whole_network(
    db: GraphDatabaseInterface = Depends(get_graph_db_connection),
) -> Subnet:
    """Return full network of nodes and edges from the database."""
    return db.get_whole_network()


@app.get("/network/summary")
def get_network_summary(
    db: GraphDatabaseInterface = Depends(get_graph_db_connection),
) -> dict[str, int]:
    """Count nodes and edges."""
    return db.get_network_summary()


@app.delete("/network", status_code=status.HTTP_205_RESET_CONTENT)
def reset_whole_network(
    db_graph: GraphDatabaseInterface = Depends(get_graph_db_connection),
    db_history: GraphHistoryDatabaseInterface = Depends(
        get_graph_history_db_connection
    ),
    user: UserRead = Depends(get_current_user),
) -> None:
    """Delete all nodes and edges. Be careful!"""
    db_graph.reset_whole_network()
    # TODO: add graph history logging


### /subnet/ ###


@app.put("/subnet")
def update_subnet(
    subnet: Subnet,
    db_graph: GraphDatabaseInterface = Depends(get_graph_db_connection),
    db_history: GraphHistoryDatabaseInterface = Depends(
        get_graph_history_db_connection
    ),
    user: UserRead = Depends(get_current_user),
) -> Subnet:
    """Add missing nodes and edges and update existing ones (given IDs)."""
    out_subnet = db_graph.update_subnet(subnet)
    # TODO: add graph history logging
    return out_subnet


@app.get("/subnet/{node_id}")
def get_induced_subnet(
    node_id: NodeId,
    levels: Annotated[int, Query(get=0)] = 2,
    db: GraphDatabaseInterface = Depends(get_graph_db_connection),
) -> Subnet:
    """Return the subnet induced from a particular element with an optional limit number of connections.
    If no neighbour is found, a singleton subnet with a single node is returned from the provided ID.
    """
    return db.get_induced_subnet(node_id, levels)


### /nodes/ ###


@app.get("/nodes")
def search_nodes(
    node_type: list[NodeType] | NodeType = Query(None),
    title: str | None = None,
    scope: str | None = None,
    status: list[NodeStatus] | NodeStatus = Query(None),
    tags: list[str] | None = Query(None),
    description: str | None = None,
    db: GraphDatabaseInterface = Depends(get_graph_db_connection),
) -> list[NodeBase]:
    """Search in nodes on a field by field level."""
    return db.search_nodes(
        node_type=node_type,
        title=title,
        scope=scope,
        status=status,
        tags=tags,
        description=description,
    )


### /node/ ###


@app.get("/node/random")
def get_random_node(
    node_type: NodeType | None = None,
    db: GraphDatabaseInterface = Depends(get_graph_db_connection),
) -> NodeBase:
    """Return a random node with optional node_type."""
    return db.get_random_node(node_type)


@app.get("/node/{node_id}")
def get_node(
    node_id: NodeId, db: GraphDatabaseInterface = Depends(get_graph_db_connection)
) -> NodeBase:
    """Return the node associated with the provided ID."""
    return db.get_node(node_id)


@app.post("/node", status_code=status.HTTP_201_CREATED)
def create_node(
    node: NodeBase,
    db_graph: GraphDatabaseInterface = Depends(get_graph_db_connection),
    db_history: GraphHistoryDatabaseInterface = Depends(
        get_graph_history_db_connection
    ),
    user: UserRead = Depends(get_current_user),
) -> NodeBase:
    """Create a node."""
    node_out = db_graph.create_node(node)
    # logger.info(f"User {user.username} created node {node_out.node_id}")
    db_history.log_event(
        GraphHistoryEvent(
            username=user.username,
            event_type=OperationType.create,
            node_id=node.node_id,
            payload=node.model_dump(),
        )
    )
    return node_out


@app.delete("/node/{node_id}")
def delete_node(
    node_id: NodeId,
    db_graph: GraphDatabaseInterface = Depends(get_graph_db_connection),
    db_history: GraphHistoryDatabaseInterface = Depends(
        get_graph_history_db_connection
    ),
    user: UserRead = Depends(get_current_user),
):
    """Delete the node with provided ID."""
    db_graph.delete_node(node_id)
    db_history.log_event(
        GraphHistoryEvent(
            username=user.username, event_type=OperationType.delete, node_id=node_id
        )
    )


@app.put("/node")
def update_node(
    node: PartialNodeBase,
    db_graph: GraphDatabaseInterface = Depends(get_graph_db_connection),
    db_history: GraphHistoryDatabaseInterface = Depends(
        get_graph_history_db_connection
    ),
    user: UserRead = Depends(get_current_user),
) -> NodeBase:
    """Update the properties of an existing node."""
    out_node = db_graph.update_node(node)
    db_history.log_event(
        GraphHistoryEvent(
            username=user.username,
            event_type=OperationType.update,
            node_id=node.node_id,
            payload=node.model_dump(),
        )
    )
    return out_node


### /edges/ ###


@app.get("/edges")
def get_edge_list(
    db: GraphDatabaseInterface = Depends(get_graph_db_connection),
) -> list[EdgeBase]:
    """Return all edges in the database."""
    return db.get_edge_list()


@app.post("/edges/find")
def find_edges(
    source_id: NodeId = None,
    target_id: NodeId = None,
    edge_type: EdgeType = None,
    db: GraphDatabaseInterface = Depends(get_graph_db_connection),
) -> list[EdgeBase]:
    """Return the edge associated with the provided ID."""
    return db.find_edges(source_id=source_id, target_id=target_id, edge_type=edge_type)


### /edge/ ###


@app.get("/edge/{source_id}/{target_id}")
def get_edge(
    source_id: NodeId,
    target_id: NodeId,
    db: GraphDatabaseInterface = Depends(get_graph_db_connection),
) -> EdgeBase:
    """Return the edge associated with the provided ID."""
    return db.get_edge(source_id, target_id)


@app.post("/edge", status_code=201)
def create_edge(
    edge: EdgeBase,
    db_graph: GraphDatabaseInterface = Depends(get_graph_db_connection),
    db_history: GraphHistoryDatabaseInterface = Depends(
        get_graph_history_db_connection
    ),
    user: UserRead = Depends(get_current_user),
) -> EdgeBase:
    """Create an edge."""
    out_edge = db_graph.create_edge(edge)
    db_history.log_event(
        GraphHistoryEvent(
            username=user.username,
            event_type=OperationType.create,
            source_id=edge.source,
            target_id=edge.target,
            payload=edge.model_dump(),
        )
    )
    return out_edge


@app.delete("/edge/{source_id}/{target_id}")
def delete_edge(
    source_id: NodeId,
    target_id: NodeId,
    edge_type: EdgeType | None = None,
    db_graph: GraphDatabaseInterface = Depends(get_graph_db_connection),
    db_history: GraphHistoryDatabaseInterface = Depends(
        get_graph_history_db_connection
    ),
    user: UserRead = Depends(get_current_user),
):
    """Delete the edge between two nodes and for an optional edge_type."""
    db_graph.delete_edge(source_id, target_id, edge_type)
    db_history.log_event(
        GraphHistoryEvent(
            username=user.username,
            event_type=OperationType.create,
            source_id=source_id,
            target_id=target_id,
        )
    )


@app.put("/edge")
def update_edge(
    edge: EdgeBase,
    db_graph: GraphDatabaseInterface = Depends(get_graph_db_connection),
    db_history: GraphHistoryDatabaseInterface = Depends(
        get_graph_history_db_connection
    ),
    user: UserRead = Depends(get_current_user),
) -> EdgeBase:
    """Update the properties of an edge."""
    out_edge = db_graph.update_edge(edge)
    db_history.log_event(
        GraphHistoryEvent(
            username=user.username,
            event_type=OperationType.create,
            source_id=edge.source,
            target_id=edge.target,
            payload=edge.model_dump(),
        )
    )
    return out_edge


### others ###


@app.post("/migrate_label_to_property")
def migrate_label_to_property(
    request: MigrateLabelRequest, db: JanusGraphDB = Depends(get_graph_db_connection)
):
    """Migrate the label of each vertex to a property called 'property_name'."""
    property_name = request.property_name
    try:
        print(f"Starting migration with property_name: {property_name}")  # Added line
        db.migrate_label_to_property(property_name)
        print("Migration successful.")  # Added line
        return {"message": f"Successfully migrated labels to property {property_name}"}
    except Exception as e:
        print(f"Migration failed with error: {e}")  # Added line
        raise HTTPException(status_code=500, detail=str(e))

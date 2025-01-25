import os
import warnings
from pathlib import Path as PathlibPath
from typing import Annotated

from dotenv import load_dotenv
from fastapi import FastAPI, status, Query, Depends, Body, HTTPException
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
)


from database.base import DatabaseInterface
from database.janusgraph import JanusGraphDB
from database.sqlite import SQLiteDB


_env_path = PathlibPath("/app/.env") if os.getenv("DOCKER_ENV") else PathlibPath(".env")

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

if os.getenv("DOCKER_ENV"):
    _version_path = PathlibPath("/app/VERSION")
elif os.getcwd().endswith("backend"):
    _version_path = PathlibPath("../VERSION")
elif os.getcwd().endswith("objectivenet"):
    _version_path = PathlibPath("VERSION")
else:
    raise FileNotFoundError("VERSION file not found")
with open(_version_path) as f:
    __version__ = f.read().strip()

app = FastAPI(title="ObjectiveNet API", version=__version__)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_db_connection(db_type: str = os.getenv("DB_TYPE")) -> DatabaseInterface:
    if db_type == "janusgraph":
        janusgraph_host = os.getenv("JANUSGRAPH_HOST", "localhost")
        traversal_source = os.getenv("TRAVERSAL_SOURCE", "g_test")
        return JanusGraphDB(janusgraph_host, traversal_source)
    elif db_type == "sqlite":
        db_path = os.getenv("SQLITE_DB_PATH", "objectivenet-db.sqlite3")
        print(f"Using SQLite database at {db_path}")
        return SQLiteDB(db_path)
    else:
        raise ValueError(f"Unsupported DB_TYPE: {db_type}")


### root ###


@app.get("/")
async def root():
    return {"message": "Welcome to ObjectiveNet!"}


### /network/ ###


@app.get("/network")
def get_whole_network(db: DatabaseInterface = Depends(get_db_connection)) -> Subnet:
    """Return full network of nodes and edges from the database."""
    return db.get_whole_network()


@app.get("/network/summary")
def get_network_summary(
    db: DatabaseInterface = Depends(get_db_connection),
) -> dict[str, int]:
    """Count nodes and edges."""
    return db.get_network_summary()


@app.delete("/network", status_code=status.HTTP_205_RESET_CONTENT)
def reset_whole_network(db: DatabaseInterface = Depends(get_db_connection)) -> None:
    """Delete all nodes and edges. Be careful!"""
    db.reset_whole_network()


### /subnet/ ###


@app.put("/subnet")
def update_subnet(
    subnet: Subnet, db: DatabaseInterface = Depends(get_db_connection)
) -> Subnet:
    """Add missing nodes and edges and update existing ones (given IDs)."""
    return db.update_subnet(subnet)


@app.get("/subnet/{node_id}")
def get_induced_subnet(
    node_id: NodeId,
    levels: Annotated[int, Query(get=0)] = 2,
    db: DatabaseInterface = Depends(get_db_connection),
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
    db: DatabaseInterface = Depends(get_db_connection),
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
    db: DatabaseInterface = Depends(get_db_connection),
) -> NodeBase:
    """Return a random node with optional node_type."""
    return db.get_random_node(node_type)


@app.get("/node/{node_id}")
def get_node(
    node_id: NodeId, db: DatabaseInterface = Depends(get_db_connection)
) -> NodeBase:
    """Return the node associated with the provided ID."""
    return db.get_node(node_id)


@app.post("/node", status_code=status.HTTP_201_CREATED)
def create_node(
    node: NodeBase, db: DatabaseInterface = Depends(get_db_connection)
) -> NodeBase:
    """Create a node."""
    return db.create_node(node)


@app.delete("/node/{node_id}")
def delete_node(node_id: NodeId, db: DatabaseInterface = Depends(get_db_connection)):
    """Delete the node with provided ID."""
    db.delete_node(node_id)


@app.put("/node")
def update_node(
    node: PartialNodeBase, db: DatabaseInterface = Depends(get_db_connection)
) -> NodeBase:
    """Update the properties of an existing node."""
    return db.update_node(node)


### /edges/ ###


@app.get("/edges")
def get_edge_list(db: DatabaseInterface = Depends(get_db_connection)) -> list[EdgeBase]:
    """Return all edges in the database."""
    return db.get_edge_list()


@app.post("/edges/find")
def find_edges(
    source_id: NodeId = None,
    target_id: NodeId = None,
    edge_type: EdgeType = None,
    db: DatabaseInterface = Depends(get_db_connection),
) -> list[EdgeBase]:
    """Return the edge associated with the provided ID."""
    return db.find_edges(source_id=source_id, target_id=target_id, edge_type=edge_type)


### /edge/ ###


@app.get("/edge/{source_id}/{target_id}")
def get_edge(
    source_id: NodeId,
    target_id: NodeId,
    db: DatabaseInterface = Depends(get_db_connection),
) -> EdgeBase:
    """Return the edge associated with the provided ID."""
    return db.get_edge(source_id, target_id)


@app.post("/edge", status_code=201)
def create_edge(
    edge: EdgeBase, db: DatabaseInterface = Depends(get_db_connection)
) -> EdgeBase:
    """Create an edge."""
    return db.create_edge(edge)


@app.delete("/edge/{source_id}/{target_id}")
def delete_edge(
    source_id: NodeId,
    target_id: NodeId,
    edge_type: EdgeType | None = None,
    db: DatabaseInterface = Depends(get_db_connection),
):
    """Delete the edge between two nodes and for an optional edge_type."""
    db.delete_edge(source_id, target_id, edge_type)


@app.put("/edge")
def update_edge(
    edge: EdgeBase, db: DatabaseInterface = Depends(get_db_connection)
) -> EdgeBase:
    """Update the properties of an edge."""
    return db.update_edge(edge)


### others ###


@app.post("/migrate_label_to_property")
def migrate_label_to_property(
    request: MigrateLabelRequest, db: JanusGraphDB = Depends(get_db_connection)
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

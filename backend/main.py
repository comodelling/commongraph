import os
import warnings
import logging
from pathlib import Path as PathlibPath
from typing import Annotated

from dotenv import load_dotenv
from fastapi import FastAPI, status, Query, Depends
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
)


from database.base import DatabaseInterface
from database.janusgraph import JanusGraphDB


app = FastAPI(title="ObjectiveNet API", version="v0.1.3")

env_path = PathlibPath("/app/.env") if os.getenv("DOCKER_ENV") else PathlibPath(".env")

if env_path.exists():
    load_dotenv(dotenv_path=env_path)
else:
    warnings.warn(
        f".env file not found at {env_path}, using default environment variables"
    )

origins = (
    [origin.strip() for origin in os.getenv("ALLOWED_ORIGINS", "").split(",")]
    if os.getenv("ALLOWED_ORIGINS")
    else []
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


DB_TYPE = os.getenv("DB_TYPE", "janusgraph")


def get_db_connection() -> DatabaseInterface:
    if DB_TYPE == "janusgraph":
        janusgraph_host = os.getenv("JANUSGRAPH_HOST", "localhost")
        traversal_source = os.getenv("TRAVERSAL_SOURCE", "g")
        return JanusGraphDB(janusgraph_host, traversal_source)
    else:
        raise ValueError(f"Unsupported DB_TYPE: {DB_TYPE}")


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


@app.get("/nodes/random")
def get_random_node(
    node_type: NodeType | None = None,
    db: DatabaseInterface = Depends(get_db_connection),
) -> NodeBase:
    """Return a random node with optional node_type."""
    return db.get_random_node(node_type)


@app.get("/nodes/{node_id}")
def get_node(
    node_id: NodeId, db: DatabaseInterface = Depends(get_db_connection)
) -> NodeBase:
    """Return the node associated with the provided ID."""
    return db.get_node(node_id)


@app.post("/nodes", status_code=status.HTTP_201_CREATED)
def create_node(
    node: NodeBase, db: DatabaseInterface = Depends(get_db_connection)
) -> NodeBase:
    """Create a node."""
    return db.create_node(node)


@app.delete("/nodes/{node_id}")
def delete_node(node_id: NodeId, db: DatabaseInterface = Depends(get_db_connection)):
    """Delete the node with provided ID."""
    db.delete_node(node_id)


@app.put("/nodes")
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


@app.get("/edges/{source_id}/{target_id}")
def get_edge(
    source_id: NodeId,
    target_id: NodeId,
    db: DatabaseInterface = Depends(get_db_connection),
) -> EdgeBase:
    """Return the edge associated with the provided ID."""
    return db.get_edge(source_id, target_id)


@app.post("/edges/find")
def find_edges(
    source_id: NodeId = None,
    target_id: NodeId = None,
    edge_type: EdgeType = None,
    db: DatabaseInterface = Depends(get_db_connection),
) -> list[EdgeBase]:
    """Return the edge associated with the provided ID."""
    return db.find_edges(source_id=source_id, target_id=target_id, edge_type=edge_type)


@app.post("/edges", status_code=201)
def create_edge(
    edge: EdgeBase, db: DatabaseInterface = Depends(get_db_connection)
) -> EdgeBase:
    """Create an edge."""
    return db.create_edge(edge)


@app.delete("/edges/{source_id}/{target_id}")
def delete_edge(
    source_id: NodeId,
    target_id: NodeId,
    edge_type: EdgeType | None = None,
    db: DatabaseInterface = Depends(get_db_connection),
):
    """Delete the edge between two nodes and for an optional edge_type."""
    db.delete_edge(source_id, target_id, edge_type)


@app.put("/edges")
def update_edge(
    edge: EdgeBase, db: DatabaseInterface = Depends(get_db_connection)
) -> EdgeBase:
    """Update the properties of an edge."""
    return db.update_edge(edge)

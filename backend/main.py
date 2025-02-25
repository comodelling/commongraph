import os
import warnings
from pathlib import Path as PathlibPath
from typing import Annotated
import logging
import datetime
import json
import random

from dotenv import load_dotenv
from fastapi import FastAPI, status, Query, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from models import (
    NodeBase,
    EdgeBase,
    Subnet,
    NetworkExport,
    NodeType,
    NodeStatus,
    NodeId,
    EdgeType,
    PartialNodeBase,
    MigrateLabelRequest,
    User,
    UserRead,
    GraphHistoryEvent,
    RatingEvent,
    RatingType,
    LikertScale,
)
from database.base import (
    GraphDatabaseInterface,
    UserDatabaseInterface,
    GraphHistoryRelationalInterface,
    RatingHistoryRelationalInterface,
)
from database.janusgraph import JanusGraphDB
from database.postgresql import (
    UserPostgreSQLDB,
    GraphHistoryPostgreSQLDB,
    RatingHistoryPostgreSQLDB,
)
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

QUOTES_FILE = os.getenv("QUOTES_FILE", "")

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
    enable_graph_db: str = os.getenv("ENABLE_GRAPH_DB"),
) -> GraphDatabaseInterface:
    enable_graph_db = enable_graph_db.lower() in ["true", "True"]
    if enable_graph_db:
        logger.info("Using JanusGraph database")
        janusgraph_host = os.getenv("JANUSGRAPH_HOST", "localhost")
        traversal_source = os.getenv("TRAVERSAL_SOURCE", "g_test")
        return JanusGraphDB(janusgraph_host, traversal_source)
    return None


def get_user_db_connection(
    db_type: str = "postgresql",
) -> UserDatabaseInterface:
    if db_type == "postgresql":
        database_url = os.getenv("POSTGRES_DB_URL")
        print(f"Using User PostgreSQL database at {database_url}")
        return UserPostgreSQLDB(database_url)
    else:
        raise ValueError(f"Unsupported db type: {db_type} for user_db")


def get_graph_history_db_connection(
    db_type: str = "postgresql",
) -> GraphHistoryRelationalInterface:
    if db_type == "postgresql":
        database_url = os.getenv("POSTGRES_DB_URL")
        print(f"Using Graph History PostgreSQL database at {database_url}")
        return GraphHistoryPostgreSQLDB(database_url)
    else:
        raise ValueError(f"Unsupported db type: {db_type} for graph_history_db")


def get_rating_history_db_connection(
    db_type: str = "postgresql",
) -> RatingHistoryRelationalInterface:
    if db_type == "postgresql":
        database_url = os.getenv("POSTGRES_DB_URL")
        print(f"Using Rating History PostgreSQL database at {database_url}")
        return RatingHistoryPostgreSQLDB(database_url)
    else:
        raise ValueError(f"Unsupported db type: {db_type} for graph_history_db")


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
    db_history: GraphHistoryRelationalInterface = Depends(
        get_graph_history_db_connection
    ),
) -> NetworkExport:
    """Return full network of nodes and edges from the database."""
    out = db_history.get_whole_network().model_dump()
    out["objectivenet_version"] = __version__
    out["timestamp"] = datetime.datetime.now().isoformat()
    return out


@app.get("/network/summary")
def get_network_summary(
    db_history: GraphHistoryRelationalInterface = Depends(
        get_graph_history_db_connection
    ),
) -> dict[str, int]:
    """Count nodes and edges."""
    return db_history.get_network_summary()


@app.delete("/network", status_code=status.HTTP_205_RESET_CONTENT)
def reset_whole_network(
    db_graph: GraphDatabaseInterface | None = Depends(get_graph_db_connection),
    db_history: GraphHistoryRelationalInterface = Depends(
        get_graph_history_db_connection
    ),
    user: UserRead = Depends(get_current_user),
) -> None:
    """Delete all nodes and edges. Be careful!"""
    db_history.reset_whole_network(username=user.username)
    if db_graph is not None:
        db_graph.reset_whole_network()


### /subnet/ ###


@app.put("/subnet")
def update_subnet(
    subnet: Subnet,
    db_graph: GraphDatabaseInterface | None = Depends(get_graph_db_connection),
    db_history: GraphHistoryRelationalInterface = Depends(
        get_graph_history_db_connection
    ),
    user: UserRead = Depends(get_current_user),
) -> Subnet:
    """Add missing nodes and edges and update existing ones (given IDs)."""
    out_subnet = db_history.update_subnet(subnet, username=user.username)
    if db_graph is not None:
        db_graph.update_subnet(subnet)
    return out_subnet


@app.get("/subnet/{node_id}")
def get_induced_subnet(
    node_id: NodeId,
    levels: Annotated[int, Query(get=0)] = 2,
    db_graph: GraphDatabaseInterface | None = Depends(get_graph_db_connection),
    db_history: GraphHistoryRelationalInterface = Depends(
        get_graph_history_db_connection
    ),
) -> Subnet:
    """Return the subnet induced from a particular element with an optional limit number of connections.
    If no neighbour is found, a singleton subnet with a single node is returned from the provided ID.
    """
    if db_graph is not None:
        return db_graph.get_induced_subnet(node_id, levels)
    return db_history.get_induced_subnet(node_id, levels)


### /nodes/ ###


@app.get("/nodes")
def search_nodes(
    node_type: list[NodeType] | NodeType = Query(None),
    title: str | None = None,
    scope: str | None = None,
    status: list[NodeStatus] | NodeStatus = Query(None),
    tags: list[str] | None = Query(None),
    description: str | None = None,
    db_graph: GraphDatabaseInterface | None = Depends(get_graph_db_connection),
    db_history: GraphHistoryRelationalInterface = Depends(
        get_graph_history_db_connection
    ),
) -> list[NodeBase]:
    """Search in nodes on a field by field level."""
    if db_graph is not None:
        return db_graph.search_nodes(
            node_type=node_type,
            title=title,
            scope=scope,
            status=status,
            tags=tags,
            description=description,
        )
    return db_history.search_nodes(
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
    db: GraphDatabaseInterface | None = Depends(get_graph_db_connection),
    db_history: GraphHistoryRelationalInterface = Depends(
        get_graph_history_db_connection
    ),
) -> NodeBase:
    """Return a random node with optional node_type."""
    if isinstance(db, JanusGraphDB):
        return db.get_random_node(node_type)
    return db_history.get_random_node(node_type)


@app.get("/node/{node_id}")
def get_node(
    node_id: NodeId,
    db_history: GraphHistoryRelationalInterface = Depends(
        get_graph_history_db_connection
    ),
) -> NodeBase:
    """Return the node associated with the provided ID."""
    return db_history.get_node(node_id)


@app.post("/node", status_code=status.HTTP_201_CREATED)
def create_node(
    node: NodeBase,
    db_graph: GraphDatabaseInterface | None = Depends(get_graph_db_connection),
    db_history: GraphHistoryRelationalInterface = Depends(
        get_graph_history_db_connection
    ),
    user: UserRead = Depends(get_current_user),
) -> NodeBase:
    """Create a node."""
    if db_graph is not None:
        node = db_graph.create_node(node)
        # logger.info(f"User {user.username} created node {node_out.node_id} in graph database too")

    node_out = db_history.create_node(
        node, username=user.username
    )  # reuse the ID allocated from the graph database
    return node_out


@app.delete("/node/{node_id}")
def delete_node(
    node_id: NodeId,
    db_graph: GraphDatabaseInterface | None = Depends(get_graph_db_connection),
    db_history: GraphHistoryRelationalInterface = Depends(
        get_graph_history_db_connection
    ),
    user: UserRead = Depends(get_current_user),
):
    """Delete the node with provided ID."""
    db_history.delete_node(node_id, username=user.username)
    if db_graph is not None:
        db_graph.delete_node(node_id)


@app.put("/node")
def update_node(
    node: PartialNodeBase,
    db_graph: GraphDatabaseInterface | None = Depends(get_graph_db_connection),
    db_history: GraphHistoryRelationalInterface = Depends(
        get_graph_history_db_connection
    ),
    user: UserRead = Depends(get_current_user),
) -> NodeBase:
    """Update the properties of an existing node."""
    node_out = db_history.update_node(node, username=user.username)
    if db_graph is not None:
        db_graph.update_node(node)
    return node_out


@app.get("/node/{node_id}/history")
def get_node_history(
    node_id: NodeId,
    db_history: GraphHistoryRelationalInterface = Depends(
        get_graph_history_db_connection
    ),
) -> list[GraphHistoryEvent]:
    """Return the history of the node associated with the provided ID."""
    return db_history.get_node_history(node_id)


### /edges/ ###


@app.get("/edges")
def get_edge_list(
    db_history: GraphHistoryRelationalInterface = Depends(
        get_graph_history_db_connection
    ),
) -> list[EdgeBase]:
    """Return all edges in the database."""
    return db_history.get_edge_list()


@app.post("/edges/find")
def find_edges(
    source_id: NodeId = None,
    target_id: NodeId = None,
    edge_type: EdgeType = None,
    db_history: GraphHistoryRelationalInterface = Depends(
        get_graph_history_db_connection
    ),
) -> list[EdgeBase]:
    """Return the edge associated with the provided ID."""
    return db_history.find_edges(
        source_id=source_id, target_id=target_id, edge_type=edge_type
    )


### /edge/ ###


@app.get("/edge/{source_id}/{target_id}")
def get_edge(
    source_id: NodeId,
    target_id: NodeId,
    db_history: GraphHistoryRelationalInterface = Depends(
        get_graph_history_db_connection
    ),
) -> EdgeBase:
    """Return the edge associated with the provided ID."""
    return db_history.get_edge(source_id, target_id)


@app.post("/edge", status_code=201)
def create_edge(
    edge: EdgeBase,
    db_graph: GraphDatabaseInterface | None = Depends(get_graph_db_connection),
    db_history: GraphHistoryRelationalInterface = Depends(
        get_graph_history_db_connection
    ),
    user: UserRead = Depends(get_current_user),
) -> EdgeBase:
    """Create an edge."""
    out_edge = db_history.create_edge(edge, username=user.username)
    if db_graph is not None:
        db_graph.create_edge(edge)
    return out_edge


@app.delete("/edge/{source_id}/{target_id}")
def delete_edge(
    source_id: NodeId,
    target_id: NodeId,
    edge_type: EdgeType | None = None,
    db_graph: GraphDatabaseInterface | None = Depends(get_graph_db_connection),
    db_history: GraphHistoryRelationalInterface = Depends(
        get_graph_history_db_connection
    ),
    user: UserRead = Depends(get_current_user),
):
    """Delete the edge between two nodes and for an optional edge_type."""
    db_history.delete_edge(source_id, target_id, edge_type, username=user.username)
    if db_graph is not None:
        db_graph.delete_edge(source_id, target_id, edge_type)


@app.put("/edge")
def update_edge(
    edge: EdgeBase,
    db_graph: GraphDatabaseInterface | None = Depends(get_graph_db_connection),
    db_history: GraphHistoryRelationalInterface = Depends(
        get_graph_history_db_connection
    ),
    user: UserRead = Depends(get_current_user),
) -> EdgeBase:
    """Update the properties of an edge."""
    out_edge = db_history.update_edge(edge, username=user.username)
    if db_graph is not None:
        db_graph.update_edge(edge)
    return out_edge


@app.get("/edge/{source_id}/{target_id}/history")
def get_edge_history(
    source_id: NodeId,
    target_id: NodeId,
    db_history: GraphHistoryRelationalInterface = Depends(
        get_graph_history_db_connection
    ),
) -> list[GraphHistoryEvent]:
    """Return the history of the edge associated with the provided source and target IDs."""
    return db_history.get_edge_history(source_id, target_id)


### ratings ###


@app.post("/rating/log", status_code=201)
def log_rating(
    rating: RatingEvent,
    db: RatingHistoryRelationalInterface = Depends(get_rating_history_db_connection),
    user: UserRead = Depends(get_current_user),
) -> RatingEvent:
    """
    Log a rating event. The username will be set from the authenticated user.
    """
    rating.username = user.username
    return db.log_rating(rating)


@app.get("/rating/node/{node_id}")
def get_node_rating(
    node_id: int,
    rating_type: RatingType = RatingType.support,
    db: RatingHistoryRelationalInterface = Depends(get_rating_history_db_connection),
    user: UserRead = Depends(get_current_user),
) -> RatingEvent | None:
    """
    Retrieve a user's rating for a node.
    """
    return db.get_node_rating(node_id, rating_type, user.username)


@app.get("/ratings/node/")
def get_node_ratings(
    node_id: int,
    rating_type: RatingType = RatingType.support,
    db: RatingHistoryRelationalInterface = Depends(get_rating_history_db_connection),
) -> dict:
    """
    Retrieve all ratings for a given node.
    """
    ratings = db.get_node_ratings(node_id, rating_type)
    # Convert each RatingEvent to dict.
    return {"ratings": ratings}


@app.get("/rating/edge")
def get_edge_rating(
    source_id: int,
    target_id: int,
    rating_type: RatingType,
    db: RatingHistoryRelationalInterface = Depends(get_rating_history_db_connection),
    user: UserRead = Depends(get_current_user),
) -> RatingEvent | None:
    """
    Retrieve a user's rating for an edge.
    """
    return db.get_edge_rating(source_id, target_id, rating_type, user.username)


@app.get("/rating/node/{node_id}/median")
def get_node_median_rating(
    node_id: int,
    rating_type: RatingType = RatingType.support,
    db: RatingHistoryRelationalInterface = Depends(get_rating_history_db_connection),
) -> dict | None:
    """
    Retrieve the median rating for a given node.
    """
    median = db.get_node_median_rating(node_id, rating_type)
    return {"median_rating": median}


@app.get("/rating/edge/median")
def get_edge_median_rating(
    source_id: int,
    target_id: int,
    rating_type: RatingType,
    db: RatingHistoryRelationalInterface = Depends(get_rating_history_db_connection),
) -> dict | None:
    """
    Retrieve the median rating for a given edge.
    """
    logger.warning("Function may not be working as expected")
    median = db.get_edge_median_rating(source_id, target_id, rating_type)
    return {"median_rating": median}


@app.get("/rating/nodes/median")
def get_nodes_median_ratings(
    node_ids: list[NodeId] = Query(
        ..., alias="node_ids[]", description="List of node IDs"
    ),
    rating_type: RatingType = RatingType.support,
    db: RatingHistoryRelationalInterface = Depends(get_rating_history_db_connection),
) -> dict[int, dict | None]:
    """
    Retrieve the median ratings for multiple nodes.
    Returns a mapping: { node_id: {'median_rating': <value> } }.
    If a node doesn't have ratings, the value will be None.
    """
    start_time = datetime.datetime.now()
    medians = db.get_nodes_median_ratings(node_ids, rating_type)
    duration = datetime.datetime.now() - start_time
    duration_ms = duration.total_seconds() * 1000
    logger.info(
        f"Retrieved median ratings for ({len(node_ids)}) nodes in {duration_ms:.2f}ms"
    )
    return {
        node_id: {"median_rating": (median.value if median is not None else None)}
        for node_id, median in medians.items()
    }


### others ###


@app.post("/migrate_label_to_property")
def migrate_label_to_property(
    request: MigrateLabelRequest, db: JanusGraphDB = Depends(get_graph_db_connection)
):
    """Migrate the label of each vertex to a property called 'property_name'."""
    property_name = request.property_name
    try:
        # Added line
        print(f"Starting migration with property_name: {property_name}")
        db.migrate_label_to_property(property_name)
        print("Migration successful.")  # Added line
        return {"message": f"Successfully migrated labels to property {property_name}"}
    except Exception as e:
        print(f"Migration failed with error: {e}")  # Added line
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/quote")
def get_random_quote():
    """Return a random quote from the quotes file.
    The quotes file is specified in the QUOTES_FILE environment variable, which should be a path to a JSON file.
    The JSON file should contain a list of dictionaries, each with a "quote" key and optional "author" and "where" keys.
    """
    if not os.path.exists(QUOTES_FILE):
        logger.warning("Quotes file not found")
        raise HTTPException(status_code=404, detail="Quotes file not found")

    with open(QUOTES_FILE, "r", encoding="utf-8") as file:
        try:
            quotes = json.load(file)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON format: {e}")
            raise HTTPException(status_code=500, detail="Invalid JSON format")

    if not quotes:
        logger.error("No quotes found")
        raise HTTPException(status_code=404, detail="No quotes found")

    random_quote = random.choice(quotes)
    return random_quote

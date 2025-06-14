import os
from typing import Annotated
import logging
import datetime
import json
import random

from fastapi import Query, Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from backend.settings import settings
from backend.version import __version__
from backend.db.connections import (
    get_graph_db,
    get_graph_history_db,
    get_rating_history_db
)
from backend.models import (
    NodeId,
    MigrateLabelRequest,
    UserRead,
    RatingEvent,
    RatingType,
)
from backend.db.base import (
    GraphDatabaseInterface,
    GraphHistoryRelationalInterface,
    RatingHistoryRelationalInterface,
)
from backend.db.janusgraph import JanusGraphDB
from backend.api.auth import router as auth_router
from backend.api.users import router as users_router
from backend.api.nodes import router as nodes_router
from backend.api.edges import router as edges_router
from backend.api.graph import router as graph_router
from backend.api.auth import get_current_user
from backend.config import (PLATFORM_NAME, NODE_TYPE_PROPS, EDGE_TYPE_PROPS, EDGE_TYPE_BETWEEN,
                    NODE_TYPE_STYLE, EDGE_TYPE_STYLE)
from backend.dynamic_models import (DynamicSubnet)

logger = logging.getLogger(__name__)

QUOTES_FILE = settings.QUOTES_FILE
origins = settings.ALLOWED_ORIGINS

app = FastAPI(title="CommonGraph API", version=__version__)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(users_router)
app.include_router(nodes_router)
app.include_router(edges_router)
app.include_router(graph_router)

@app.get("/config")
def get_config():
    # Here we combine both properties and styles for each type.
    node_types = {
        nt: {"properties": list(props), "style": NODE_TYPE_STYLE.get(nt, {})}
        for nt, props in NODE_TYPE_PROPS.items()
    }
    edge_types = {
        et: {"properties": list(props),
             "between": EDGE_TYPE_BETWEEN.get(et, None),
             "style": EDGE_TYPE_STYLE.get(et, {})}
        for et, props in EDGE_TYPE_PROPS.items()
    }
    return {
        "platform_name": PLATFORM_NAME,
        "node_types": node_types,  #TODO: might deprecate and use graph/schema instead
        "edge_types": edge_types,
    }
    

@app.get("/schema")
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


### root ###


@app.get("/")
async def root():
    return {"message": "CommonGraph API", "version": __version__}


### /subnet/ ###


@app.put("/subnet")
def update_subnet(
    subnet: DynamicSubnet,
    db_graph: GraphDatabaseInterface | None = Depends(get_graph_db),
    db_history: GraphHistoryRelationalInterface = Depends(
        get_graph_history_db
    ),
    user: UserRead = Depends(get_current_user),
)  -> DynamicSubnet:
    """Add missing nodes and edges and update existing ones (given IDs)."""
    out_subnet = db_history.update_subnet(subnet, username=user.username)
    if db_graph is not None:
        db_graph.update_subnet(subnet)
    return out_subnet


@app.get("/subnet/{node_id}")
def get_induced_subnet(
    node_id: NodeId,
    levels: Annotated[int, Query(get=0)] = 2,
    db_graph: GraphDatabaseInterface | None = Depends(get_graph_db),
    db_history: GraphHistoryRelationalInterface = Depends(
        get_graph_history_db
    ),
) -> DynamicSubnet:
    """Return the subnet induced from a particular element with an optional limit number of connections.
    If no neighbour is found, a singleton subnet with a single node is returned from the provided ID.
    """
    if db_graph is not None:
        return db_graph.get_induced_subnet(node_id, levels)
    return db_history.get_induced_subnet(node_id, levels)



### ratings ###

@app.post("/rating/log", status_code=201)
def log_rating(
    rating: RatingEvent,
    db: RatingHistoryRelationalInterface = Depends(get_rating_history_db),
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
    db: RatingHistoryRelationalInterface = Depends(get_rating_history_db),
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
    db: RatingHistoryRelationalInterface = Depends(get_rating_history_db),
) -> dict:
    """
    Retrieve all ratings for a given node.
    """
    ratings = db.get_node_ratings(node_id, rating_type)
    # Convert each RatingEvent to dict.
    return {"ratings": ratings}


@app.get("/rating/edge/{source_id}/{target_id}")
def get_edge_rating(
    source_id: int,
    target_id: int,
    rating_type: RatingType,
    db: RatingHistoryRelationalInterface = Depends(get_rating_history_db),
    user: UserRead = Depends(get_current_user),
) -> RatingEvent | None:
    """
    Retrieve a user's rating for an edge.
    """
    return db.get_edge_rating(source_id, target_id, rating_type, user.username)


@app.get("/ratings/edge/{source_id}/{target_id}")
def get_edge_ratings(
    source_id: int,
    target_id: int,
    rating_type: RatingType = RatingType.causal_strength,
    db: RatingHistoryRelationalInterface = Depends(get_rating_history_db),
) -> dict:
    """
    Retrieve all ratings for a given edge.
    """
    ratings = db.get_edge_ratings(source_id, target_id, rating_type)
    # Convert each RatingEvent to dict.
    return {"ratings": ratings}


@app.get("/rating/node/{node_id}/median")
def get_node_median_rating(
    node_id: int,
    rating_type: RatingType = RatingType.support,
    db: RatingHistoryRelationalInterface = Depends(get_rating_history_db),
) -> dict | None:
    """
    Retrieve the median rating for a given node.
    """
    median = db.get_node_median_rating(node_id, rating_type)
    return {"median_rating": median}


@app.get("/rating/edge/median/")
def get_edge_median_rating(
    source_id: int,
    target_id: int,
    rating_type: RatingType,
    db: RatingHistoryRelationalInterface = Depends(get_rating_history_db),
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
    db: RatingHistoryRelationalInterface = Depends(get_rating_history_db),
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


@app.get("/rating/edges/median")
def get_edges_median_ratings(
    edge_ids: list[str] = Query(
        ..., alias="edge_ids[]", description="List of edges in form 'source-target'"
    ),
    rating_type: RatingType = RatingType.causal_strength,
    db: RatingHistoryRelationalInterface = Depends(get_rating_history_db),
) -> dict[str, dict | None]:
    """
    Retrieve the median ratings for multiple edges.
    Returns a mapping: { "source-target": {"median_rating": <value>} }.
    If an edge doesn't have ratings, the value will be None.
    """
    start_time = datetime.datetime.now()
    # Convert string keys to a list of (source_id, target_id) for the DB method
    edges = []
    for key in edge_ids:
        src_str, tgt_str = key.split("-")
        edges.append((int(src_str), int(tgt_str)))

    medians = db.get_edges_median_ratings(edges, rating_type)
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


### others ###


@app.post("/migrate_label_to_property")
def migrate_label_to_property(
    request: MigrateLabelRequest, db: JanusGraphDB = Depends(get_graph_db)
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

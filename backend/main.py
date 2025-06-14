import os
import logging
import json
import random

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from backend.settings import settings
from backend.version import __version__
from backend.db.connections import get_graph_db
from backend.models.fixed import MigrateLabelRequest

from backend.db.janusgraph import JanusGraphDB
from backend.api.auth import router as auth_router
from backend.api.users import router as users_router
from backend.api.nodes import router as nodes_router
from backend.api.edges import router as edges_router
from backend.api.graph import router as graph_router
from backend.config import (PLATFORM_NAME, NODE_TYPE_PROPS, EDGE_TYPE_PROPS, EDGE_TYPE_BETWEEN,
                    NODE_TYPE_STYLE, EDGE_TYPE_STYLE)

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


@app.get("/")
async def root():
    return {"message": "CommonGraph API", "version": __version__}


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

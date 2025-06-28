import os
import logging
import json
import random
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from backend.version import __version__
from backend.settings import settings
from backend.api.auth import router as auth_router
from backend.api.users import router as users_router
from backend.api.nodes import router as nodes_router
from backend.api.edges import router as edges_router
from backend.api.graph import router as graph_router
from backend.api.schema import router as schema_router
from backend.config import (PLATFORM_NAME, NODE_TYPE_PROPS, EDGE_TYPE_PROPS, EDGE_TYPE_BETWEEN,
                            NODE_TYPE_STYLE, EDGE_TYPE_STYLE, NODE_TYPE_POLLS, EDGE_TYPE_POLLS)
from backend.db.postgresql import UserPostgreSQLDB
from backend.utils.security import hash_password
from backend.models.fixed import UserCreate

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- startup ---
    # seed the initial admin if needed
    admin_user = settings.INITIAL_ADMIN_USER
    admin_pw   = settings.INITIAL_ADMIN_PASSWORD
    if admin_user and admin_pw:
        db = UserPostgreSQLDB(settings.POSTGRES_DB_URL)
        if not db.get_user(admin_user):
            db.create_user(
                UserCreate(
                    username=admin_user,
                    password=admin_pw,
                    is_active=True,
                    is_admin=True,
                    security_question=None,
                    security_answer=None,
                )
            )
    
    # Initialize schema in database
    from backend.db.connections import get_graph_history_db
    from backend.schema_manager import SchemaManager
    from sqlmodel import Session
    
    try:
        graph_db = get_graph_history_db()
        with Session(graph_db.engine) as session:
            manager = SchemaManager(session)
            manager.ensure_schema_in_db("system")
            logger.info("Schema initialized in database")
    except Exception as e:
        logger.error(f"Failed to initialize schema: {e}")
    
    yield


app = FastAPI(title="CommonGraph API", 
              version=__version__,
              lifespan=lifespan)

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
app.include_router(schema_router)




@app.get("/")
async def root():
    return {"message": "CommonGraph API", "version": __version__}


@app.get("/config")
def get_config():
    # Here we combine both properties and styles for each type.
    from backend.config import CONFIG_VERSION, CONFIG_HASH
    
    node_types = {
        nt: {"properties": list(props),
             "polls": NODE_TYPE_POLLS.get(nt, {}),
             "style": NODE_TYPE_STYLE.get(nt, {})}
        for nt, props in NODE_TYPE_PROPS.items()
    }
    edge_types = {
        et: {"properties": list(props),
             "between": EDGE_TYPE_BETWEEN.get(et, None),
             "polls": EDGE_TYPE_POLLS.get(et, {}),
             "style": EDGE_TYPE_STYLE.get(et, {})}
        for et, props in EDGE_TYPE_PROPS.items()
    }
    return {
        "platform_name": PLATFORM_NAME,
        "node_types": node_types,
        "edge_types": edge_types,
        "schema_version": CONFIG_VERSION,
        "schema_hash": CONFIG_HASH,
    }


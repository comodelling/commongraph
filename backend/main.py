import os
import logging
import json
import random
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware

from backend.version import __version__
from backend.settings import settings
from backend.api.auth import router as auth_router, get_current_user
from backend.api.users import router as users_router
from backend.api.nodes import router as nodes_router
from backend.api.edges import router as edges_router
from backend.api.graph import router as graph_router
from backend.api.schema import router as schema_router
from backend.api.scopes import router as scopes_router
from backend.api.tags import router as tags_router
from backend.config import (
    PLATFORM_DESCRIPTION,
    PLATFORM_NAME,
    NODE_TYPE_PROPS,
    EDGE_TYPE_PROPS,
    EDGE_TYPE_BETWEEN,
    NODE_TYPE_STYLE,
    EDGE_TYPE_STYLE,
    NODE_TYPE_POLLS,
    EDGE_TYPE_POLLS,
    PLATFORM_TAGLINE,
    LICENSE,
)
from backend.utils.permissions import get_permission_summary
from backend.models.fixed import UserRead
from backend.db.postgresql import UserPostgreSQLDB
from backend.utils.security import hash_password
from backend.models.fixed import UserCreate

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- startup ---
    # seed the initial admin if needed
    admin_user = settings.INITIAL_ADMIN_USER
    admin_pw = settings.INITIAL_ADMIN_PASSWORD
    if admin_user and admin_pw:
        db = UserPostgreSQLDB(settings.POSTGRES_DB_URL)
        if not db.get_user(admin_user):
            logger.info(f"Creating initial super admin user: {admin_user}")
            db.create_user(
                UserCreate(
                    username=admin_user,
                    password=admin_pw,
                    is_active=True,
                    is_admin=True,
                    is_super_admin=True,  # First user gets super admin privileges
                    security_question=None,
                    security_answer=None,
                )
            )
            logger.info(f"Initial super admin user created successfully: {admin_user}")
        else:
            logger.info(f"Initial admin user already exists: {admin_user}")

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


app = FastAPI(title="CommonGraph API", version=__version__, lifespan=lifespan)

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
app.include_router(scopes_router)
app.include_router(tags_router)


@app.get("/")
async def root():
    return {"message": "CommonGraph API", "version": __version__}


@app.get("/config")
def get_config(current_user: UserRead = Depends(get_current_user)):
    # Here we combine both properties and styles for each type.
    from backend.config import get_current_config_version, get_current_config_hash

    node_types = {
        nt: {
            "properties": list(props),
            "polls": NODE_TYPE_POLLS.get(nt, {}),
            "style": NODE_TYPE_STYLE.get(nt, {}),
        }
        for nt, props in NODE_TYPE_PROPS.items()
    }
    edge_types = {
        et: {
            "properties": list(props),
            "between": EDGE_TYPE_BETWEEN.get(et, None),
            "polls": EDGE_TYPE_POLLS.get(et, {}),
            "style": EDGE_TYPE_STYLE.get(et, {}),
        }
        for et, props in EDGE_TYPE_PROPS.items()
    }
    from backend.config import ALLOW_SIGNUP, SIGNUP_REQUIRES_TOKEN

    return {
        "platform_name": PLATFORM_NAME,
        "platform_tagline": PLATFORM_TAGLINE,
        "platform_description": PLATFORM_DESCRIPTION,
        "node_types": node_types,
        "edge_types": edge_types,
        "schema_version": get_current_config_version(),
        "schema_hash": get_current_config_hash(),
        "permissions": get_permission_summary(current_user),
        "allow_signup": ALLOW_SIGNUP,
        "signup_requires_token": SIGNUP_REQUIRES_TOKEN,
        "license": LICENSE,
    }

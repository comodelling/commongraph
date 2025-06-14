import logging

from backend.settings import settings
from backend.db.base import GraphHistoryRelationalInterface, RatingHistoryRelationalInterface, UserDatabaseInterface
from backend.db.postgresql import GraphHistoryPostgreSQLDB, RatingHistoryPostgreSQLDB, UserPostgreSQLDB
from backend.db.janusgraph import JanusGraphDB

logger = logging.getLogger(__name__)


def get_graph_db():
    if settings.ENABLE_GRAPH_DB:
        logger.info("Using JanusGraph database")
        return JanusGraphDB(settings.JANUSGRAPH_HOST, settings.TRAVERSAL_SOURCE)
    logger.info("Graph DB disabled")
    return None


def get_user_db(
    db_type: str = "postgresql",
) -> UserDatabaseInterface:
    if db_type == "postgresql":
        database_url = settings.POSTGRES_DB_URL
        logger.info(f"Using User PostgreSQL database at {database_url}")
        return UserPostgreSQLDB(database_url)
    else:
        raise ValueError(f"Unsupported db type: {db_type} for user_db")


def get_graph_history_db(
    db_type: str = "postgresql",
) -> GraphHistoryRelationalInterface:
    if db_type == "postgresql":
        database_url = settings.POSTGRES_DB_URL
        logger.info(f"Using Graph History PostgreSQL database at {database_url}")
        return GraphHistoryPostgreSQLDB(database_url)
    else:
        raise ValueError(f"Unsupported db type: {db_type} for graph_history_db")


def get_rating_history_db(
    db_type: str = "postgresql",
) -> RatingHistoryRelationalInterface:
    if db_type == "postgresql":
        database_url = settings.POSTGRES_DB_URL
        logger.info(f"Using Rating History PostgreSQL database at {database_url}")
        return RatingHistoryPostgreSQLDB(database_url)
    else:
        raise ValueError(f"Unsupported db type: {db_type} for graph_history_db")


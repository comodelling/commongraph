import os
import pytest
import datetime
from fastapi.testclient import TestClient

from backend.main import app
from backend.api.auth import get_current_user

# Configure test database and secret key
POSTGRES_TEST_DB_URL = os.getenv(
    "POSTGRES_TEST_DB_URL", "postgresql://postgres:postgres@localhost/testdb"
)
os.environ["POSTGRES_DB_URL"] = POSTGRES_TEST_DB_URL
os.environ["SECRET_KEY"] = "testsecret"

# Override authentication dependency for testing
from backend.models.fixed import UserRead


@pytest.fixture(scope="module", autouse=True)
def setup_test_env():
    """Set up test environment including authentication override and database reset."""
    from backend.db.postgresql import RatingHistoryPostgreSQLDB

    # Override authentication
    app.dependency_overrides[get_current_user] = lambda: UserRead(
        username="testuser",
        preferences={},
        is_active=True,
        is_admin=False,
        is_super_admin=False,
    )

    # Reset database
    db = RatingHistoryPostgreSQLDB(POSTGRES_TEST_DB_URL)
    db.reset_table()

    yield

    # Cleanup
    db.reset_table()
    app.dependency_overrides.pop(get_current_user, None)


client = TestClient(app)


def test_log_and_get_node_rating():
    # Create a rating for a node
    rating_data = {
        "entity_type": "node",
        "node_id": 1,
        "poll_label": "support",
        "rating": 4.0,
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
    }
    response = client.post("/nodes/1/ratings", json=rating_data)
    assert response.status_code == 201
    logged = response.json()
    assert logged["node_id"] == 1
    assert logged["rating"] == 4.0
    assert logged["entity_type"] == "node"
    assert logged["username"] == "testuser"

    # Retrieve the logged rating
    response = client.get("/node/ratings/1")
    assert response.status_code == 200
    fetched = response.json()
    assert fetched["node_id"] == 1
    assert fetched["rating"] == 4.0
    assert fetched["username"] == "testuser"


def test_node_median_rating():
    # Log additional ratings for the node to test median computation
    ratings = [
        {
            "entity_type": "node",
            "node_id": 2,
            "poll_label": "support",
            "rating": 5.0,
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        },
        {
            "entity_type": "node",
            "node_id": 2,
            "poll_label": "support",
            "rating": 3.0,
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        },
        {
            "entity_type": "node",
            "node_id": 2,
            "poll_label": "support",
            "rating": 4.0,
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        },
    ]
    for r in ratings:
        client.post("/nodes/2/ratings", json=r)

    response = client.get("/nodes/2/ratings/median")
    assert response.status_code == 200
    data = response.json()
    # Ratings [3.0, 4.0, 5.0] median is 4.0
    assert data["median_rating"] == 4.0


def test_log_and_get_edge_rating():
    # Create a rating for an edge
    rating_data = {
        "entity_type": "edge",
        "node_id": None,  # not used for edge rating
        "source_id": 10,
        "target_id": 20,
        "poll_label": "necessity",
        "rating": 2.0,
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
    }
    response = client.post("/edges/10/20/ratings", json=rating_data)
    assert response.status_code == 201
    logged = response.json()
    assert logged["source_id"] == 10
    assert logged["target_id"] == 20
    assert logged["rating"] == 2.0
    assert logged["entity_type"] == "edge"
    assert logged["username"] == "testuser"

    # Retrieve the logged edge rating (explicitly pass poll_label)
    response = client.get(
        "/edges/10/20/ratings",
        params={"poll_label": "necessity"},
    )
    assert response.status_code == 200
    fetched = response.json()
    assert fetched["source_id"] == 10
    assert fetched["target_id"] == 20
    assert fetched["rating"] == 2.0
    assert fetched["username"] == "testuser"


def test_edge_median_rating():
    # Log additional ratings for the edge
    ratings = [
        {
            "entity_type": "edge",
            "source_id": 30,
            "target_id": 40,
            "poll_label": "sufficiency",
            "rating": 4.0,
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        },
        {
            "entity_type": "edge",
            "source_id": 30,
            "target_id": 40,
            "poll_label": "sufficiency",
            "rating": 1.0,
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        },
        {
            "entity_type": "edge",
            "source_id": 30,
            "target_id": 40,
            "poll_label": "sufficiency",
            "rating": 3.0,
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        },
    ]
    for r in ratings:
        client.post("/edges/30/40/ratings", json=r)

    response = client.get(
        "/edges/30/40/ratings/median",
        params={"poll_label": "sufficiency"},
    )
    assert response.status_code == 200
    data = response.json()
    # Ratings [1.0, 3.0, 4.0] median is 3.0
    assert data["median_rating"] == 3.0

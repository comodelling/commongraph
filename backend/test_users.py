import os
import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.db.postgresql import UserPostgreSQLDB

# Configure test database and secret key
POSTGRES_TEST_DB_URL = os.getenv(
    "POSTGRES_TEST_DB_URL", "postgresql://postgres:postgres@localhost/testdb"
)
os.environ["POSTGRES_DB_URL"] = POSTGRES_TEST_DB_URL
os.environ["SECRET_KEY"] = "testsecret"

client = TestClient(app)


@pytest.fixture(scope="module", autouse=True)
def reset_db():
    db = UserPostgreSQLDB(POSTGRES_TEST_DB_URL)
    db.reset_user_table()
    yield
    db.reset_user_table()


def test_signup():
    signup_data = {
        "user": {
            "username": "testuser",
            "password": "securepassword",
            "preferences": {"theme": "dark"},
            "security_question": "What is your favorite color?",
            "security_answer": "Blue",
        }
    }
    response = client.post("/auth/signup", json=signup_data)
    assert response.status_code == 200
    json_resp = response.json()
    assert json_resp["username"] == "testuser"
    assert json_resp["preferences"]["theme"] == "dark"


def test_login():
    # Ensure the user is created
    signup_data = {
        "user": {
            "username": "testuser",
            "password": "securepassword",
            "preferences": {"theme": "dark"},
            "security_question": "What is your favorite color?",
            "security_answer": "Blue",
        }
    }
    client.post("/auth/signup", json=signup_data)

    # Use form data since OAuth2PasswordRequestForm expects application/x-www-form-urlencoded
    login_data = {"username": "testuser", "password": "securepassword"}
    response = client.post("/auth/login", data=login_data)
    assert response.status_code == 200
    json_resp = response.json()
    assert "access_token" in json_resp


def test_get_current_user():
    # Ensure the user is created
    signup_data = {
        "user": {
            "username": "testuser",
            "password": "securepassword",
            "preferences": {"theme": "dark"},
            "security_question": "What is your favorite color?",
            "security_answer": "Blue",
        }
    }
    client.post("/auth/signup", json=signup_data)

    # Log in to get the access token
    login_data = {"username": "testuser", "password": "securepassword"}
    login_resp = client.post("/auth/login", data=login_data)
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    me_resp = client.get("/users/me", headers=headers)
    assert me_resp.status_code == 200
    json_me = me_resp.json()
    assert json_me["username"] == "testuser"


def test_logout():
    response = client.post("/auth/logout")
    assert response.status_code == 200
    assert response.json()["msg"] == "Logout successful"

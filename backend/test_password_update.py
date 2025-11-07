import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.db.postgresql import UserPostgreSQLDB
from backend.models.fixed import UserCreate
from backend.utils.security import hash_password, verify_password
import os

# Configure test database (same as other tests)
POSTGRES_TEST_DB_URL = os.getenv(
    "POSTGRES_TEST_DB_URL", "postgresql://postgres:postgres@localhost/testdb"
)
os.environ["POSTGRES_DB_URL"] = POSTGRES_TEST_DB_URL
os.environ["SECRET_KEY"] = "testsecret"

client = TestClient(app)


@pytest.fixture
def test_user():
    """Create a test user for password update tests"""
    db = UserPostgreSQLDB(POSTGRES_TEST_DB_URL)
    test_username = "test_password_user"
    test_password = "testpassword123"

    # Reset database to ensure clean state
    db.reset_user_table()

    # Create test user
    user = UserCreate(
        username=test_username,
        password=test_password,
        is_active=True,
        is_admin=False,
        security_question="What is your favorite color?",
        security_answer="blue",
    )

    created_user = db.create_user(user)

    yield {
        "username": test_username,
        "password": test_password,
        "user": created_user,
    }

    # Cleanup after test
    db.reset_user_table()


def test_password_update_success(test_user):
    """Test successful password update"""
    # First, login to get a token
    login_response = client.post(
        "/auth/login",
        data={"username": test_user["username"], "password": test_user["password"]},
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]

    # Update password
    new_password = "newpassword456"
    response = client.patch(
        "/users/password",
        json={"current_password": test_user["password"], "new_password": new_password},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json()["message"] == "Password updated successfully"

    # Verify old password no longer works
    old_login_response = client.post(
        "/auth/login",
        data={"username": test_user["username"], "password": test_user["password"]},
    )
    assert old_login_response.status_code == 400

    # Verify new password works
    new_login_response = client.post(
        "/auth/login",
        data={"username": test_user["username"], "password": new_password},
    )
    assert new_login_response.status_code == 200


def test_password_update_wrong_current_password(test_user):
    """Test password update with wrong current password"""
    # First, login to get a token
    login_response = client.post(
        "/auth/login",
        data={"username": test_user["username"], "password": test_user["password"]},
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]

    # Try to update password with wrong current password
    response = client.patch(
        "/users/password",
        json={"current_password": "wrongpassword", "new_password": "newpassword456"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 400
    assert "Current password is incorrect" in response.json()["detail"]


def test_password_update_unauthorized():
    """Test password update without authentication"""
    response = client.patch(
        "/users/password",
        json={"current_password": "somepassword", "new_password": "newpassword456"},
    )

    # Without auth, user is "anonymous" which doesn't exist, returns 404
    assert response.status_code == 404
    assert "User not found" in response.json()["detail"]


def test_password_update_short_password(test_user):
    """Test password update with too short new password"""
    # First, login to get a token
    login_response = client.post(
        "/auth/login",
        data={"username": test_user["username"], "password": test_user["password"]},
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]

    # Try to update password with short new password
    response = client.patch(
        "/users/password",
        json={
            "current_password": test_user["password"],
            "new_password": "123",  # Too short
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 422  # Validation error

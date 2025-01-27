import pytest

from models import UserCreate
from database.postgresql import PostgreSQLDB
from database.base import UserDatabaseInterface


@pytest.fixture(scope="module", params=["postgresql"])
def user_db(request):
    db_type = request.param
    if db_type == "postgresql":
        db = PostgreSQLDB("postgresql://postgres:postgres@localhost/testdb")
    else:
        raise ValueError(f"Unsupported USER_DB_TYPE: {db_type}")
    yield db
    db.reset_whole_network()


def test_create_user(user_db: UserDatabaseInterface):
    user_create = UserCreate(
        username="testuser", password="securepassword", preferences={"theme": "dark"}
    )
    user_read = user_db.create_user(user_create)
    assert user_read.username == "testuser"
    assert user_read.preferences["theme"] == "dark"


def test_get_user(user_db: UserDatabaseInterface):
    username = "testuser"
    user = user_db.get_user(username)
    assert user is not None
    assert user.username == username

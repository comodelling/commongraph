from fastapi import APIRouter, Depends, HTTPException, status

from backend.db.base import UserDatabaseInterface
from backend.db.connections import get_user_db
from backend.models import User, UserRead


router = APIRouter(prefix="/users", tags=["users"])


@router.post("", status_code=status.HTTP_201_CREATED, response_model=UserRead)
def create_user(
    user: User,
    db: UserDatabaseInterface = Depends(get_user_db),
) -> UserRead:
    return db.create_user(user)

@router.get("/{username}", response_model=UserRead)
def get_user(
    username: str,
    db: UserDatabaseInterface = Depends(get_user_db),
) -> UserRead:
    user = db.get_user(username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
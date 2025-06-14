from fastapi import APIRouter, Depends, HTTPException, status

from backend.api.auth import get_current_user, get_user_db, logger, router
from backend.db.base import UserDatabaseInterface
from backend.db.connections import get_user_db
from backend.models import User, UserRead


router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserRead)
def read_current_user(current_user: UserRead = Depends(get_current_user)):
    logger.info(f"Retrieved current user: {current_user.username}")
    return current_user


@router.patch("/preferences", response_model=UserRead)
def update_preferences(
    prefs: dict,
    current_user: UserRead = Depends(get_current_user),
    db: UserDatabaseInterface = Depends(get_user_db),
):
    logger.info(f"Updating preferences for user: {current_user.username}")
    updated_user = db.update_preferences(current_user.username, prefs)
    logger.info(f"Preferences updated for user: {current_user.username}")
    return updated_user


@router.patch("/security-settings", response_model=UserRead)
def update_security_settings(
    security_settings: dict,
    current_user: UserRead = Depends(get_current_user),
    db: UserDatabaseInterface = Depends(get_user_db),
):
    logger.info(
        f"Updating security settings for user: {current_user.username}")
    user = db.get_user(current_user.username)
    if not user:
        logger.warning(
            f"User not found while updating security settings: {current_user.username}"
        )
        raise HTTPException(status_code=404, detail="User not found")
    user.security_question = security_settings.get("security_question")
    user.security_answer = security_settings.get("security_answer")
    updated_user = db.update_user(user)
    logger.info(
        f"Security settings updated for user: {current_user.username}")
    return updated_user


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

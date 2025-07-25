from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from pydantic import BaseModel, Field

from backend.api.auth import get_current_user, get_user_db, logger, router
from backend.db.base import UserDatabaseInterface
from backend.db.connections import get_user_db
from backend.models.fixed import User, UserRead
from backend.utils.security import verify_password, hash_password


router = APIRouter(prefix="/users", tags=["users"])


class UpdatePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=6)


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


@router.patch("/password", response_model=dict)
def update_password(
    password_request: UpdatePasswordRequest,
    current_user: UserRead = Depends(get_current_user),
    db: UserDatabaseInterface = Depends(get_user_db),
):
    logger.info(f"Updating password for user: {current_user.username}")
    
    # Get the full user record (including password hash)
    user = db.get_user(current_user.username)
    if not user:
        logger.warning(f"User not found while updating password: {current_user.username}")
        raise HTTPException(status_code=404, detail="User not found")
    
    # Verify current password
    if not verify_password(password_request.current_password, user.password):
        logger.warning(f"Incorrect current password for user: {current_user.username}")
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    
    # Update password with new hashed password
    user.password = hash_password(password_request.new_password)
    db.update_user(user)
    
    logger.info(f"Password updated successfully for user: {current_user.username}")
    return {"message": "Password updated successfully"}


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


@router.get("/", response_model=List[UserRead])
def list_users(
    current_user: UserRead = Depends(get_current_user),
    db: UserDatabaseInterface = Depends(get_user_db),
) -> List[UserRead]:
    if not (current_user.is_admin or current_user.is_super_admin):
        raise HTTPException(status_code=403, detail="Not authorized")
    return db.list_users()


@router.patch("/{username}/approve", response_model=UserRead)
def approve_user(
    username: str,
    current_user: UserRead = Depends(get_current_user),
    db: UserDatabaseInterface = Depends(get_user_db),
) -> UserRead:
    if not (current_user.is_admin or current_user.is_super_admin):
        raise HTTPException(status_code=403, detail="Not authorized")
    user = db.get_user(username)
    if not user:
        raise HTTPException(404, "User not found")
    user.is_active = True
    return db.update_user(user)


@router.patch("/{username}/promote", response_model=UserRead)
def promote_user(
    username: str,
    current_user: UserRead = Depends(get_current_user),
    db: UserDatabaseInterface = Depends(get_user_db),
) -> UserRead:
    if not (current_user.is_admin or current_user.is_super_admin):
        raise HTTPException(status_code=403, detail="Not authorized")
    user = db.get_user(username)
    if not user:
        raise HTTPException(404, "User not found")
    user.is_admin = True
    return db.update_user(user)


@router.patch("/{username}/demote", response_model=UserRead)
def demote_user(
    username: str,
    current_user: UserRead = Depends(get_current_user),
    db: UserDatabaseInterface = Depends(get_user_db),
) -> UserRead:
    if not (current_user.is_admin or current_user.is_super_admin):
        raise HTTPException(status_code=403, detail="Not authorized")
    user = db.get_user(username)
    if not user:
        raise HTTPException(404, "User not found")
    # Super admins cannot be demoted
    if user.is_super_admin:
        raise HTTPException(status_code=403, detail="Cannot demote super admins")
    user.is_admin = False
    return db.update_user(user)


@router.patch("/{username}/super-admin", response_model=UserRead)
def toggle_super_admin(
    username: str,
    current_user: UserRead = Depends(get_current_user),
    db: UserDatabaseInterface = Depends(get_user_db),
) -> UserRead:
    # Only existing super admins can manage super admin status
    if not current_user.is_super_admin:
        raise HTTPException(status_code=403, detail="Only super admins can manage super admin status")
    user = db.get_user(username)
    if not user:
        raise HTTPException(404, "User not found")
    user.is_super_admin = not user.is_super_admin
    # If promoting to super admin, also grant admin rights
    if user.is_super_admin:
        user.is_admin = True
    return db.update_user(user)

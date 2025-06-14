from datetime import datetime, timedelta, timezone
import os
import jwt
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel

from backend.models import UserCreate, UserRead
from db.base import UserDatabaseInterface
from db.postgresql import UserPostgreSQLDB
from utils.security import verify_password, hash_password

logger = logging.getLogger(__name__)

router = APIRouter()

SECRET_KEY = os.getenv("SECRET_KEY", "yourSecretKey")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)


def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    logger.debug(f"Access token created for data: {data}")
    return token


def create_refresh_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    )
    to_encode.update({"exp": expire})
    token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    logger.debug(f"Refresh token created for data: {data}")
    return token


def get_user_db() -> UserDatabaseInterface:
    database_url = os.getenv("POSTGRES_DB_URL")
    if not database_url:
        logger.error("Database URL not configured")
        raise HTTPException(status_code=500, detail="Database URL not configured")
    logger.debug("Creating UserPostgreSQLDB instance")
    return UserPostgreSQLDB(database_url)


@router.post("/auth/refresh")
def refresh_token(
    token: str = Depends(oauth2_scheme),  # send refresh token as bearer token
    db: UserDatabaseInterface = Depends(get_user_db),
):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            logger.warning("Refresh token payload does not contain username")
            raise HTTPException(status_code=401, detail="Invalid token")
    except jwt.PyJWTError:
        logger.warning("JWT decode failed during refresh")
        raise HTTPException(status_code=401, detail="Invalid token")

    user = db.get_user(username)
    if not user:
        logger.warning(f"User not found during token refresh: {username}")
        raise HTTPException(status_code=401, detail="User not found")

    new_access_token = create_access_token(data={"sub": username})
    new_refresh_token = create_refresh_token(data={"sub": username})
    logger.info(f"New tokens issued for user: {username}")
    return {"access_token": new_access_token, "refresh_token": new_refresh_token}


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: UserDatabaseInterface = Depends(get_user_db),
) -> UserRead:
    if not token:
        return UserRead(username="anonymous")
    logger.info("Validating current user from token")
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            logger.warning("Token payload does not contain username")
            raise credentials_exception
    except jwt.PyJWTError:
        logger.warning("JWT decode failed")
        raise credentials_exception

    user = db.get_user(username)
    if not user:
        logger.warning(f"User not found: {username}")
        raise credentials_exception
    logger.info(f"Current user validated: {username}")
    return user


@router.post("/auth/signup", response_model=UserRead)
def signup(user: UserCreate, db: UserDatabaseInterface = Depends(get_user_db)):
    logger.info(f"Signup attempt for username: {user.username}")
    created_user = db.create_user(user)
    logger.info(f"User created successfully: {created_user.username}")
    return created_user


@router.post("/auth/login")
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: UserDatabaseInterface = Depends(get_user_db),
):
    logger.info(f"Login attempt for user: {form_data.username}")
    full_user = db.get_user(form_data.username)
    if not full_user or not verify_password(form_data.password, full_user.password):
        logger.warning(f"Failed login for user: {form_data.username}")
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    access_token = create_access_token(data={"sub": full_user.username})
    refresh_token = create_refresh_token(data={"sub": full_user.username})
    logger.info(f"Access and refresh tokens issued for user: {full_user.username}")
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.get("/user/me", response_model=UserRead)
def read_current_user(current_user: UserRead = Depends(get_current_user)):
    logger.info(f"Retrieved current user: {current_user.username}")
    return current_user


@router.patch("/user/preferences", response_model=UserRead)
def update_preferences(prefs: dict, current_user: UserRead = Depends(get_current_user)):
    logger.info(f"Updating preferences for user: {current_user.username}")
    db = get_user_db()
    updated_user = db.update_preferences(current_user.username, prefs)
    logger.info(f"Preferences updated for user: {current_user.username}")
    return updated_user


@router.get("/auth/security-question")
def get_security_question(
    username: str, db: UserDatabaseInterface = Depends(get_user_db)
):
    logger.info(f"Requesting security question for username: {username}")
    user = db.get_user(username)
    if not user:
        logger.warning(f"User not found for security question: {username}")
        raise HTTPException(status_code=404, detail="User not found")
    logger.info(f"Security question retrieved for user: {username}")
    return {"security_question": user.security_question}


class VerifySecurityQuestionRequest(BaseModel):
    username: str
    answer: str


@router.post("/auth/verify-security-question")
def verify_security_question(
    request: VerifySecurityQuestionRequest,
    db: UserDatabaseInterface = Depends(get_user_db),
):
    logger.info(f"Verifying security question answer for user: {request.username}")
    user = db.get_user(request.username)
    if not user or user.security_answer.lower() != request.answer.lower():
        logger.warning(f"Incorrect security answer for user: {request.username}")
        raise HTTPException(
            status_code=400, detail="Incorrect answer to the security question"
        )
    reset_token = create_access_token(
        data={"sub": user.username}, expires_delta=timedelta(minutes=15)
    )
    logger.info(f"Security question verified for user: {request.username}")
    return {"reset_token": reset_token}


@router.patch("/user/security-settings", response_model=UserRead)
def update_security_settings(
    security_settings: dict,
    current_user: UserRead = Depends(get_current_user),
    db: UserDatabaseInterface = Depends(get_user_db),
):
    logger.info(f"Updating security settings for user: {current_user.username}")
    user = db.get_user(current_user.username)
    if not user:
        logger.warning(
            f"User not found while updating security settings: {current_user.username}"
        )
        raise HTTPException(status_code=404, detail="User not found")
    user.security_question = security_settings.get("security_question")
    user.security_answer = security_settings.get("security_answer")
    updated_user = db.update_user(user)
    logger.info(f"Security settings updated for user: {current_user.username}")
    return updated_user


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


@router.post("/auth/reset-password")
def reset_password(
    request: ResetPasswordRequest, db: UserDatabaseInterface = Depends(get_user_db)
):
    logger.info("Attempting password reset")
    try:
        payload = jwt.decode(request.token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            logger.warning("Reset token did not contain username")
            raise HTTPException(status_code=400, detail="Invalid token")
    except jwt.PyJWTError:
        logger.warning("JWT decode failed during password reset")
        raise HTTPException(status_code=400, detail="Invalid token")

    user = db.get_user(username)
    if not user:
        logger.warning(f"User not found for password reset: {username}")
        raise HTTPException(status_code=404, detail="User not found")

    user.password = hash_password(request.new_password)
    db.update_user(user)
    logger.info(f"Password reset successfully for user: {username}")
    return {"msg": "Password reset successful"}


@router.post("/auth/logout")
def logout():
    logger.info("User logout requested")
    # With JWT, logout is managed on the client side by simply deleting the token.
    return {"msg": "Logout successful"}

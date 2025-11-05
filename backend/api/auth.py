from datetime import datetime, timedelta, timezone
import os
import jwt
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel

from backend.models.fixed import (
    UserCreate,
    UserRead,
    SignupToken,
    SignupTokenRead,
    SignupTokenCreate,
)
from backend.db.base import UserDatabaseInterface
from backend.db.postgresql import UserPostgreSQLDB
from backend.utils.security import verify_password, hash_password
from backend.config import (
    ALLOW_SIGNUP,
    SIGNUP_REQUIRES_ADMIN_APPROVAL,
    SIGNUP_REQUIRES_TOKEN,
)
from sqlmodel import Session, select
from backend.db.connections import get_relational_session
import secrets


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])

SECRET_KEY = os.getenv("SECRET_KEY", "yourSecretKey")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login", auto_error=False)


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


@router.post("/refresh")
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
        return UserRead(
            username="anonymous", is_active=False, is_admin=False, is_super_admin=False
        )
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


class SignupRequest(BaseModel):
    user: UserCreate
    signup_token: str | None = None


@router.post("/signup", response_model=UserRead)
def signup(
    request: SignupRequest,
    db: UserDatabaseInterface = Depends(get_user_db),
    session: Session = Depends(get_relational_session),
):
    if not ALLOW_SIGNUP:
        raise HTTPException(status_code=403, detail="Signups are currently disabled")

    # Check if token is required
    if SIGNUP_REQUIRES_TOKEN:
        if not request.signup_token:
            raise HTTPException(status_code=400, detail="Signup token is required")

        # Validate the token
        statement = select(SignupToken).where(SignupToken.token == request.signup_token)
        signup_token = session.exec(statement).first()

        if not signup_token:
            raise HTTPException(status_code=400, detail="Invalid signup token")

        if signup_token.used_by is not None:
            raise HTTPException(
                status_code=400, detail="This signup token has already been used"
            )

        # Mark token as used
        signup_token.used_by = request.user.username
        signup_token.used_at = datetime.now(timezone.utc)
        session.add(signup_token)
        session.commit()

        logger.info(
            f"Signup token {request.signup_token[:8]}... used by {request.user.username}"
        )

    data = request.user.dict()
    data["is_active"] = not SIGNUP_REQUIRES_ADMIN_APPROVAL
    created = db.create_user(UserCreate(**data))
    # TODO: notify admin if SIGNUP_REQUIRES_ADMIN_APPROVAL
    return created


@router.post("/login")
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: UserDatabaseInterface = Depends(get_user_db),
):
    logger.info(f"Login attempt for user: {form_data.username}")
    full_user = db.get_user(form_data.username)
    if not full_user or not verify_password(form_data.password, full_user.password):
        logger.warning(f"Failed login for user: {form_data.username}")
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    if not full_user.is_active:
        raise HTTPException(status_code=403, detail="Account pending approval")
    access_token = create_access_token(data={"sub": full_user.username})
    refresh_token = create_refresh_token(data={"sub": full_user.username})
    logger.info(f"Access and refresh tokens issued for user: {full_user.username}")
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.get("/security-question")
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


@router.post("/verify-security-question")
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


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


@router.post("/reset-password")
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


# Signup token endpoints


@router.post("/admin/generate-signup-token", response_model=SignupTokenRead)
def generate_signup_token(
    token_data: SignupTokenCreate,
    current_user: UserRead = Depends(get_current_user),
    session: Session = Depends(get_relational_session),
):
    """Admin-only endpoint to generate a signup token"""
    if not current_user.is_admin and not current_user.is_super_admin:
        raise HTTPException(status_code=403, detail="Admin access required")

    # Generate a random token
    token = secrets.token_urlsafe(32)

    # Create the token record
    signup_token = SignupToken(
        token=token,
        created_by=current_user.username,
        created_at=datetime.now(timezone.utc),
        notes=token_data.notes,
    )

    session.add(signup_token)
    session.commit()
    session.refresh(signup_token)

    logger.info(f"Signup token generated by {current_user.username}")
    return signup_token


@router.get("/admin/signup-tokens", response_model=list[SignupTokenRead])
def list_signup_tokens(
    current_user: UserRead = Depends(get_current_user),
    session: Session = Depends(get_relational_session),
):
    """Admin-only endpoint to list all signup tokens"""
    if not current_user.is_admin and not current_user.is_super_admin:
        raise HTTPException(status_code=403, detail="Admin access required")

    statement = select(SignupToken)
    tokens = session.exec(statement).all()
    return tokens


@router.delete("/admin/signup-tokens/{token}")
def delete_signup_token(
    token: str,
    current_user: UserRead = Depends(get_current_user),
    session: Session = Depends(get_relational_session),
):
    """Admin-only endpoint to delete a signup token"""
    if not current_user.is_admin and not current_user.is_super_admin:
        raise HTTPException(status_code=403, detail="Admin access required")

    statement = select(SignupToken).where(SignupToken.token == token)
    signup_token = session.exec(statement).first()

    if not signup_token:
        raise HTTPException(status_code=404, detail="Token not found")

    session.delete(signup_token)
    session.commit()

    logger.info(f"Signup token deleted by {current_user.username}")
    return {"msg": "Token deleted successfully"}


@router.post("/logout")
def logout():
    logger.info("User logout requested")
    # With JWT, logout is managed on the client side by simply deleting the token.
    return {"msg": "Logout successful"}

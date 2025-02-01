from datetime import datetime, timedelta
import os
import jwt

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

from models import UserCreate, UserRead
from database.base import UserDatabaseInterface
from database.postgresql import PostgreSQLDB
from utils.security import (
    verify_password,
    hash_password,
)  # Add or implement verify_password if not already present

router = APIRouter()

SECRET_KEY = os.getenv("SECRET_KEY", "yourSecretKey")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_user_db() -> UserDatabaseInterface:
    database_url = os.getenv("POSTGRES_DB_URL")
    if not database_url:
        raise HTTPException(status_code=500, detail="Database URL not configured")
    return PostgreSQLDB(database_url)


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: UserDatabaseInterface = Depends(get_user_db),
) -> UserRead:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception

    user = db.get_user(username)
    if not user:
        raise credentials_exception
    return user


@router.post("/auth/signup", response_model=UserRead)
def signup(user: UserCreate, db: UserDatabaseInterface = Depends(get_user_db)):
    # Note: db.create_user already hashes the password.
    return db.create_user(user)


@router.post("/auth/login")
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: UserDatabaseInterface = Depends(get_user_db),
):
    # Assuming get_user returns a full user record with a hashed password attribute.
    full_user = db.get_user(form_data.username)
    if not full_user or not verify_password(form_data.password, full_user.password):
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    access_token = create_access_token(data={"sub": full_user.username})
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/user/me", response_model=UserRead)
def read_current_user(current_user: UserRead = Depends(get_current_user)):
    return current_user


@router.post("/auth/logout")
def logout():
    # With JWT, logout is managed on the client side by simply deleting the token.
    return {"msg": "Logout successful"}

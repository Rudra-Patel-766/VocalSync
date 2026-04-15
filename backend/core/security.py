from datetime import datetime, timedelta
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status

import firebase_admin
from firebase_admin import auth, credentials

from core.config import settings


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# -------------------------
# Password Utilities
# -------------------------

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


# -------------------------
# JWT Token Handling
# -------------------------

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):

    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )

    return encoded_jwt


def verify_token(token: str) -> dict:

    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )

        return payload

    except JWTError:

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


# -------------------------
# Firebase Initialization
# -------------------------

def initialize_firebase():

    if firebase_admin._apps:
        return

    # Check env variables
    if not settings.FIREBASE_PRIVATE_KEY:
        raise RuntimeError(
            "FIREBASE_PRIVATE_KEY is missing. Check your .env configuration."
        )

    cred = credentials.Certificate({
        "type": "service_account",
        "project_id": settings.FIREBASE_PROJECT_ID,
        "private_key_id": settings.FIREBASE_PRIVATE_KEY_ID,
        "private_key": settings.FIREBASE_PRIVATE_KEY.replace("\\n", "\n"),
        "client_email": settings.FIREBASE_CLIENT_EMAIL,
        "client_id": settings.FIREBASE_CLIENT_ID,
        "token_uri": "https://oauth2.googleapis.com/token",
    })

    firebase_admin.initialize_app(cred)


# -------------------------
# Firebase Token Verification
# -------------------------

def verify_firebase_token(id_token: str) -> dict:

    try:

        decoded_token = auth.verify_id_token(id_token)

        return decoded_token

    except Exception as e:

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid Firebase token: {str(e)}",
        )

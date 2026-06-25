"""
Authentication configuration and JWT handling
"""

import os
import bcrypt
from datetime import datetime, timedelta
from typing import Optional
import jwt
from jwt import PyJWTError
import logging

logger = logging.getLogger(__name__)

SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7


def hash_password(password: str) -> str:
    """Hash a password using bcrypt directly"""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against its hashed version"""
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token
    
    Args:
        data: Payload to encode
        expires_delta: Token expiration time delta
        
    Returns:
        Encoded JWT token
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    """
    Create a JWT refresh token
    
    Args:
        data: Payload to encode
        
    Returns:
        Encoded JWT refresh token
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> dict:
    """
    Decode and validate a JWT token.
    Accepts sub as either int or string for backward compatibility.
    """
    try:
        # options: don't enforce sub type — we normalise it ourselves
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
            options={"verify_sub": False},
        )
        # Normalise sub to string so callers always get a consistent type
        if "sub" in payload:
            payload["sub"] = str(payload["sub"])
        return payload
    except PyJWTError as e:
        logger.warning(f"Invalid token: {str(e)}")
        raise


def get_token_expiry(token: str) -> Optional[datetime]:
    """Get the expiration time of a token"""
    try:
        payload = decode_token(token)
        exp_timestamp = payload.get("exp")
        if exp_timestamp:
            return datetime.utcfromtimestamp(exp_timestamp)
    except PyJWTError:
        pass
    return None

"""
FastAPI dependencies for authentication and request handling
"""

import logging
from typing import Optional
from fastapi import Depends, HTTPException, status, Request
from jwt import PyJWTError
from sqlalchemy.orm import Session

from config.auth import decode_token
from db.database import get_db
from db import auth_crud
from db.models import User, UserRole

logger = logging.getLogger(__name__)


async def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
) -> User:
    """
    Dependency to extract and validate JWT token from request.
    Returns current authenticated user or raises HTTPException.
    """
    # Try to get token from Authorization header
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Parse Bearer token
    parts = auth_header.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = parts[1]
    
    try:
        payload = decode_token(token)
        user_id_str = payload.get("sub")
        if user_id_str is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
                headers={"WWW-Authenticate": "Bearer"},
            )
        # Convert string to int
        try:
            user_id = int(user_id_str)
        except (ValueError, TypeError):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = auth_crud.get_user_by_id(db, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )
    
    if not user.is_approved:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account is pending admin approval",
        )
    
    return user


# ─── Role-based dependency factories ─────────────────────────────────────────

def require_roles(*roles: UserRole):
    """
    Dependency factory that enforces the caller has one of the given roles.

    Usage:
        Depends(require_roles(UserRole.ADMIN, UserRole.COMPLIANCE_OFFICER))
    """
    def _check(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in roles:
            allowed = ", ".join(r.value for r in roles)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required role(s): {allowed}",
            )
        return current_user
    return _check


# Pre-built role guards used in route decorators
require_admin = require_roles(UserRole.ADMIN)

# Roles that can create/modify compliance content
require_write_access = require_roles(
    UserRole.ADMIN,
    UserRole.COMPLIANCE_OFFICER,
)

# Roles that can read/export compliance content (all authenticated roles)
require_read_access = require_roles(
    UserRole.ADMIN,
    UserRole.COMPLIANCE_OFFICER,
    UserRole.SECURITY_LEAD,
    UserRole.EXECUTIVE,
    UserRole.AUDITOR,
)


async def get_current_user_optional(
    request: Request,
    db: Session = Depends(get_db),
) -> Optional[User]:
    """
    Optional dependency - returns current user if authenticated, None otherwise.
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        return None
    
    try:
        return await get_current_user(request, db)
    except HTTPException:
        return None


async def get_request_context(request: Request):
    """Get request context including IP and user agent"""
    return {
        "ip_address": request.client.host if request.client else None,
        "user_agent": request.headers.get("user-agent", ""),
    }

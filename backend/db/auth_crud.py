"""
CRUD operations for authentication and user management
"""

from sqlalchemy.orm import Session
from sqlalchemy import func
from db.models import User, UserSession, UserRole
from config.auth import hash_password, verify_password
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


def create_user(
    db: Session,
    email: str,
    username: str,
    password: str,
    full_name: str = None,
    role: UserRole = UserRole.COMPLIANCE_OFFICER,
    is_approved: bool = False,   # new users require admin approval
) -> User:
    """Create a new user — unapproved by default"""
    existing = db.query(User).filter(
        (User.email == email) | (User.username == username)
    ).first()
    if existing:
        raise ValueError(f"User with email '{email}' or username '{username}' already exists")

    hashed_password = hash_password(password)
    db_user = User(
        email=email,
        username=username,
        password_hash=hashed_password,
        full_name=full_name,
        role=role,
        is_approved=is_approved,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    logger.info(f"Created new user: {username} ({email}) role={role} approved={is_approved}")
    return db_user


def get_user_by_email(db: Session, email: str) -> User:
    """Get user by email"""
    return db.query(User).filter(User.email == email).first()


def get_user_by_username(db: Session, username: str) -> User:
    """Get user by username"""
    return db.query(User).filter(User.username == username).first()


def get_user_by_id(db: Session, user_id: int) -> User:
    """Get user by ID"""
    return db.query(User).filter(User.id == user_id).first()


def authenticate_user(db: Session, email: str, password: str) -> User:
    """
    Authenticate user with email and password.
    Raises ValueError with a specific code if account is pending approval.
    Returns None if credentials are wrong.
    """
    user = get_user_by_email(db, email)
    if not user:
        logger.warning(f"Login attempt with non-existent email: {email}")
        return None

    if not user.is_active:
        logger.warning(f"Login attempt for inactive user: {email}")
        return None

    if not verify_password(password, user.password_hash):
        logger.warning(f"Failed login attempt for user: {email}")
        return None

    if not user.is_approved:
        logger.warning(f"Login attempt for unapproved user: {email}")
        raise PermissionError("pending_approval")

    # Update last login
    user.last_login = datetime.utcnow()
    db.commit()
    return user


def approve_user(db: Session, user_id: int) -> User:
    """Admin approves a pending user account"""
    user = get_user_by_id(db, user_id)
    if not user:
        raise ValueError(f"User {user_id} not found")
    user.is_approved = True
    db.commit()
    logger.info(f"Approved user account: {user.username}")
    return user


def reject_user(db: Session, user_id: int) -> None:
    """Admin rejects (deletes) a pending user account"""
    user = get_user_by_id(db, user_id)
    if not user:
        raise ValueError(f"User {user_id} not found")
    db.delete(user)
    db.commit()
    logger.info(f"Rejected and removed user: {user.username}")


def get_pending_users(db: Session) -> list:
    """List all users pending admin approval"""
    return db.query(User).filter(User.is_approved == False, User.is_active == True).all()


def create_user_session(
    db: Session,
    user_id: int,
    access_token: str,
    refresh_token: str,
    expires_at: datetime,
    ip_address: str = None,
    user_agent: str = None,
) -> UserSession:
    """Create a user session"""
    session = UserSession(
        user_id=user_id,
        access_token=access_token,
        refresh_token=refresh_token,
        expires_at=expires_at,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def get_session_by_access_token(db: Session, token: str) -> UserSession:
    """Get user session by access token"""
    return db.query(UserSession).filter(
        UserSession.access_token == token,
        UserSession.is_active == True
    ).first()


def get_session_by_refresh_token(db: Session, token: str) -> UserSession:
    """Get user session by refresh token"""
    return db.query(UserSession).filter(
        UserSession.refresh_token == token,
        UserSession.is_active == True
    ).first()


def revoke_session(db: Session, session_id: int) -> None:
    """Revoke a user session"""
    session = db.query(UserSession).filter(UserSession.id == session_id).first()
    if session:
        session.is_active = False
        db.commit()
        logger.info(f"Revoked session {session_id}")


def revoke_user_sessions(db: Session, user_id: int) -> None:
    """Revoke all sessions for a user (logout all devices)"""
    db.query(UserSession).filter(
        UserSession.user_id == user_id,
        UserSession.is_active == True
    ).update({"is_active": False})
    db.commit()
    logger.info(f"Revoked all sessions for user {user_id}")


def update_user_password(db: Session, user_id: int, new_password: str) -> User:
    """Update user password"""
    user = get_user_by_id(db, user_id)
    if not user:
        raise ValueError(f"User {user_id} not found")
    
    user.password_hash = hash_password(new_password)
    db.commit()
    logger.info(f"Updated password for user {user_id}")
    return user


def update_user(db: Session, user_id: int, **kwargs) -> User:
    """Update user profile"""
    user = get_user_by_id(db, user_id)
    if not user:
        raise ValueError(f"User {user_id} not found")
    
    for key, value in kwargs.items():
        if hasattr(user, key) and key not in ["id", "password_hash", "created_at"]:
            setattr(user, key, value)
    
    user.updated_at = datetime.utcnow()
    db.commit()
    return user


def list_users(db: Session, skip: int = 0, limit: int = 100) -> list:
    """List all users"""
    return db.query(User).offset(skip).limit(limit).all()


def count_users(db: Session) -> int:
    """Count total users"""
    return db.query(func.count(User.id)).scalar()

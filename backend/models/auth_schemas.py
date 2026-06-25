"""
Pydantic schemas for authentication
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
from db.models import UserRole


class UserCreate(BaseModel):
    """Schema for creating a new user"""
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=128)
    password: str = Field(..., min_length=8, description="Password must be at least 8 characters")
    full_name: Optional[str] = None


class UserLogin(BaseModel):
    """Schema for user login"""
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """Schema for user response (safe, no password)"""
    id: int
    email: str
    username: str
    full_name: Optional[str]
    role: UserRole
    is_active: bool
    is_verified: bool
    is_approved: bool
    created_at: datetime
    last_login: Optional[datetime]

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    """Schema for login response"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds
    user: UserResponse


class TokenRefresh(BaseModel):
    """Schema for token refresh request"""
    refresh_token: str


class PasswordChange(BaseModel):
    """Schema for changing password"""
    old_password: str
    new_password: str = Field(..., min_length=8)
    confirm_password: str


class UserUpdate(BaseModel):
    """Schema for updating user profile"""
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None

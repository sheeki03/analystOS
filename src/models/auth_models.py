"""
Authentication Models

Pydantic models for authentication endpoints:
- Login request/response
- Token refresh
- User info
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    """Login request payload."""
    username: str = Field(..., min_length=1, max_length=100)
    password: str = Field(..., min_length=1)


class LoginResponse(BaseModel):
    """Login response with access token."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds until access token expires


class RefreshResponse(BaseModel):
    """Token refresh response."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class LogoutResponse(BaseModel):
    """Logout response."""
    message: str = "Successfully logged out"


class UserInfo(BaseModel):
    """User information returned by /auth/me."""
    user_id: str
    username: str
    email: Optional[str] = None
    role: str = "user"
    created_at: Optional[datetime] = None


class TokenPayload(BaseModel):
    """JWT token payload structure."""
    sub: str  # user_id
    username: str
    role: str = "user"
    exp: datetime  # expiration time
    iat: datetime  # issued at
    jti: Optional[str] = None  # JWT ID for tracking


class User(BaseModel):
    """User model for internal use."""
    user_id: str
    username: str
    email: Optional[str] = None
    password_hash: str
    role: str = "user"
    created_at: datetime
    updated_at: datetime
    is_active: bool = True


class AuthError(BaseModel):
    """Authentication error response."""
    detail: str
    error_code: Optional[str] = None

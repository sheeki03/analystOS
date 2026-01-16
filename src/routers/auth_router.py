"""
Authentication Router

JWT-based authentication with rotating refresh tokens:
- POST /auth/login - Authenticate and get tokens
- POST /auth/refresh - Rotate refresh token and get new access token
- POST /auth/logout - Revoke refresh token
- GET /auth/me - Get current user info

Token Strategy:
- Access tokens: 15m TTL, stateless JWT, sent in Authorization: Bearer header
- Refresh tokens: 30-day absolute + 7-day sliding window, stored server-side,
  sent in httpOnly cookie, rotated on every refresh

Cookie Configuration:
- Dev: path=/api/auth, SameSite=Lax, Secure=False, HttpOnly=True
- Prod: path=/auth, SameSite=Lax, Secure=True, HttpOnly=True
"""

import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from src.models.auth_models import (
    LoginRequest,
    LoginResponse,
    LogoutResponse,
    RefreshResponse,
    TokenPayload,
    UserInfo,
)
from src.services.token_store import (
    get_token_store_instance,
    generate_token,
    generate_family_id,
    hash_token,
    TokenStoreBase,
)

logger = logging.getLogger(__name__)

# JWT Configuration
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-secret-key-change-in-production")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15

# Cookie Configuration
COOKIE_NAME = "refresh_token"
COOKIE_PATH = os.getenv("COOKIE_PATH", "/api/auth")  # Dev: /api/auth, Prod: /auth
COOKIE_SECURE = os.getenv("APP_ENV", "development") == "production"
COOKIE_SAMESITE = "lax"
COOKIE_HTTPONLY = True
COOKIE_DOMAIN = os.getenv("COOKIE_DOMAIN")  # None for dev, api.analystos.com for prod

# Security scheme
security = HTTPBearer(auto_error=False)

router = APIRouter(prefix="/auth", tags=["Authentication"])


# ============================================================================
# User Store (In-memory for now - replace with database in production)
# ============================================================================

# Temporary in-memory user store
# In production, this should be replaced with a proper database
_users: dict[str, dict] = {}


def _init_demo_users() -> None:
    """Initialize demo users for development."""
    demo_password = "demo123"
    password_hash = bcrypt.hashpw(demo_password.encode(), bcrypt.gensalt()).decode()

    _users["demo"] = {
        "user_id": "user-demo-001",
        "username": "demo",
        "email": "demo@example.com",
        "password_hash": password_hash,
        "role": "user",
        "created_at": datetime.now(timezone.utc),
        "is_active": True,
    }

    _users["admin"] = {
        "user_id": "user-admin-001",
        "username": "admin",
        "email": "admin@example.com",
        "password_hash": password_hash,
        "role": "admin",
        "created_at": datetime.now(timezone.utc),
        "is_active": True,
    }


# Initialize demo users on module load
_init_demo_users()


def get_user_by_username(username: str) -> Optional[dict]:
    """Get user by username."""
    return _users.get(username)


def verify_password(plain_password: str, password_hash: str) -> bool:
    """Verify password against hash."""
    try:
        return bcrypt.checkpw(plain_password.encode(), password_hash.encode())
    except ValueError:
        # Malformed hash
        return False


# ============================================================================
# JWT Token Functions
# ============================================================================

def create_access_token(user_id: str, username: str, role: str) -> tuple[str, datetime]:
    """
    Create a JWT access token.

    Returns:
        Tuple of (token, expiration_datetime)
    """
    now = datetime.now(timezone.utc)
    expires = now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    payload = {
        "sub": user_id,
        "username": username,
        "role": role,
        "exp": expires,
        "iat": now,
    }

    token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return token, expires


def decode_access_token(token: str) -> Optional[TokenPayload]:
    """
    Decode and validate a JWT access token.

    Returns:
        TokenPayload if valid, None if invalid/expired
    """
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return TokenPayload(
            sub=payload["sub"],
            username=payload["username"],
            role=payload.get("role", "user"),
            exp=datetime.fromtimestamp(payload["exp"], tz=timezone.utc),
            iat=datetime.fromtimestamp(payload["iat"], tz=timezone.utc),
            jti=payload.get("jti"),
        )
    except JWTError as e:
        logger.debug(f"JWT decode error: {e}")
        return None


# ============================================================================
# Cookie Functions
# ============================================================================

def set_refresh_cookie(response: Response, token: str) -> None:
    """Set refresh token cookie with secure settings."""
    # Calculate max_age: 30 days in seconds
    max_age = 30 * 24 * 60 * 60

    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        max_age=max_age,
        path=COOKIE_PATH,
        domain=COOKIE_DOMAIN,
        secure=COOKIE_SECURE,
        httponly=COOKIE_HTTPONLY,
        samesite=COOKIE_SAMESITE,
    )


def clear_refresh_cookie(response: Response) -> None:
    """Clear refresh token cookie."""
    response.delete_cookie(
        key=COOKIE_NAME,
        path=COOKIE_PATH,
        domain=COOKIE_DOMAIN,
    )


def get_refresh_token_from_cookie(request: Request) -> Optional[str]:
    """Extract refresh token from cookie."""
    return request.cookies.get(COOKIE_NAME)


# ============================================================================
# Dependencies
# ============================================================================

async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> TokenPayload:
    """
    Dependency to get current authenticated user from JWT.

    Raises:
        HTTPException 401 if not authenticated or token invalid
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token_payload = decode_access_token(credentials.credentials)
    if token_payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return token_payload


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Optional[TokenPayload]:
    """
    Dependency to optionally get current user.

    Returns None if not authenticated (doesn't raise exception).
    """
    if credentials is None:
        return None

    return decode_access_token(credentials.credentials)


def get_token_store() -> TokenStoreBase:
    """Dependency to get token store instance."""
    return get_token_store_instance()


# ============================================================================
# Routes
# ============================================================================

@router.post("/login", response_model=LoginResponse)
async def login(
    request: LoginRequest,
    response: Response,
    token_store: TokenStoreBase = Depends(get_token_store),
) -> LoginResponse:
    """
    Authenticate user and issue tokens.

    - Access token returned in response body
    - Refresh token set in httpOnly cookie
    """
    # Find user
    user = get_user_by_username(request.username)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    # Verify password
    if not verify_password(request.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    # Check if user is active
    if not user.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is disabled",
        )

    # Create access token
    access_token, expires = create_access_token(
        user_id=user["user_id"],
        username=user["username"],
        role=user["role"],
    )

    # Create refresh token with new family
    refresh_token = generate_token()
    family_id = generate_family_id()

    await token_store.store(
        user_id=user["user_id"],
        token=refresh_token,
        family_id=family_id,
    )

    # Set refresh token cookie
    set_refresh_cookie(response, refresh_token)

    logger.info(f"User {user['username']} logged in")

    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post("/refresh", response_model=RefreshResponse)
async def refresh(
    request: Request,
    response: Response,
    token_store: TokenStoreBase = Depends(get_token_store),
) -> RefreshResponse:
    """
    Refresh access token using refresh token from cookie.

    - Validates refresh token
    - Rotates refresh token (issues new one, marks old as used)
    - Detects token reuse (theft) and revokes entire family
    """
    # Get refresh token from cookie
    refresh_token = get_refresh_token_from_cookie(request)
    if refresh_token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No refresh token provided",
        )

    # Validate refresh token
    validation = await token_store.validate(refresh_token)

    if not validation.is_valid:
        clear_refresh_cookie(response)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    # Check for token reuse (potential theft)
    if validation.is_used:
        # Token was already used - this indicates potential theft
        # Revoke entire token family
        logger.warning(
            f"Refresh token reuse detected for user {validation.user_id}, "
            f"family {validation.family_id}. Revoking family."
        )
        await token_store.revoke_family(validation.family_id)
        clear_refresh_cookie(response)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked due to suspicious activity",
        )

    # Get user info
    user = None
    for u in _users.values():
        if u["user_id"] == validation.user_id:
            user = u
            break

    if user is None:
        clear_refresh_cookie(response)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    # Deny refresh for disabled users
    if not user.get("is_active", True):
        clear_refresh_cookie(response)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User is disabled",
        )

    # Rotate refresh token
    new_refresh_token, _ = await token_store.rotate(
        old_token=refresh_token,
        user_id=validation.user_id,
        family_id=validation.family_id,
    )

    # Update last_used_at for sliding window
    new_token_hash = hash_token(new_refresh_token)
    await token_store.update_last_used(new_token_hash)

    # Create new access token
    access_token, expires = create_access_token(
        user_id=user["user_id"],
        username=user["username"],
        role=user["role"],
    )

    # Set new refresh token cookie
    set_refresh_cookie(response, new_refresh_token)

    logger.debug(f"Refreshed tokens for user {user['username']}")

    return RefreshResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post("/logout", response_model=LogoutResponse)
async def logout(
    request: Request,
    response: Response,
    token_store: TokenStoreBase = Depends(get_token_store),
    current_user: Optional[TokenPayload] = Depends(get_current_user_optional),
) -> LogoutResponse:
    """
    Logout user by revoking refresh token.

    - Revokes refresh token server-side
    - Clears refresh token cookie
    """
    # Get refresh token from cookie
    refresh_token = get_refresh_token_from_cookie(request)

    if refresh_token:
        # Revoke the refresh token
        token_hash = hash_token(refresh_token)
        await token_store.revoke(token_hash)

    # Clear cookie
    clear_refresh_cookie(response)

    if current_user:
        logger.info(f"User {current_user.username} logged out")

    return LogoutResponse(message="Successfully logged out")


@router.get("/me", response_model=UserInfo)
async def get_me(
    current_user: TokenPayload = Depends(get_current_user),
) -> UserInfo:
    """
    Get current user information.

    Requires valid access token in Authorization header.
    """
    # Find user details
    user = None
    for u in _users.values():
        if u["user_id"] == current_user.sub:
            user = u
            break

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return UserInfo(
        user_id=user["user_id"],
        username=user["username"],
        email=user.get("email"),
        role=user["role"],
        created_at=user.get("created_at"),
    )


@router.post("/logout-all")
async def logout_all(
    response: Response,
    current_user: TokenPayload = Depends(get_current_user),
    token_store: TokenStoreBase = Depends(get_token_store),
) -> dict:
    """
    Logout from all devices by revoking all refresh tokens.

    Requires valid access token.
    """
    count = await token_store.revoke_all(current_user.sub)
    clear_refresh_cookie(response)

    logger.info(f"User {current_user.username} logged out from all devices ({count} tokens revoked)")

    return {
        "message": f"Successfully logged out from all devices",
        "tokens_revoked": count,
    }

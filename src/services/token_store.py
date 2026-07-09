"""
Token Store Service

Manages refresh tokens with:
- Server-side storage (Redis prod, in-memory dev)
- 30-day absolute expiry + 7-day sliding window
- Token rotation on every refresh
- Family tracking for token theft detection
- Reuse detection triggers family revocation

Token Lifecycle:
1. Login → Create token with family_id, store server-side
2. Refresh → Validate token, mark as used, issue new token in same family
3. Reuse detection → If used token is presented, revoke entire family
4. Logout → Revoke single token
"""

import hashlib
import logging
import os
import secrets
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# Token timing constants (from plan)
ABSOLUTE_EXPIRY_DAYS = 30
SLIDING_WINDOW_DAYS = 7
TOKEN_BYTES = 32  # 256-bit tokens


@dataclass
class RefreshToken:
    """Refresh token data structure."""
    token_hash: str  # SHA-256 hash of the actual token
    user_id: str
    family_id: str
    issued_at: datetime
    expires_at: datetime
    last_used_at: datetime
    used: bool = False


@dataclass
class TokenValidationResult:
    """Result of token validation."""
    is_valid: bool
    is_used: bool = False
    family_id: Optional[str] = None
    user_id: Optional[str] = None
    token_hash: Optional[str] = None


def hash_token(token: str) -> str:
    """Create SHA-256 hash of token for storage."""
    return hashlib.sha256(token.encode()).hexdigest()


def generate_token() -> str:
    """Generate a cryptographically secure refresh token."""
    return secrets.token_urlsafe(TOKEN_BYTES)


def generate_family_id() -> str:
    """Generate a unique family ID for token chains."""
    return str(uuid.uuid4())


class TokenStoreBase(ABC):
    """Abstract base class for token stores."""

    @abstractmethod
    async def store(
        self,
        user_id: str,
        token: str,
        family_id: str,
    ) -> RefreshToken:
        """
        Store a new refresh token.

        Args:
            user_id: The user this token belongs to
            token: The raw token string (will be hashed for storage)
            family_id: The token family ID

        Returns:
            RefreshToken data object
        """
        pass

    @abstractmethod
    async def validate(self, token: str) -> TokenValidationResult:
        """
        Validate a refresh token.

        Checks:
        1. Token exists
        2. Not expired (absolute 30-day)
        3. Within sliding window (7-day from last use)
        4. Whether it has been used (for reuse detection)

        Returns:
            TokenValidationResult with validation status
        """
        pass

    @abstractmethod
    async def mark_used(self, token_hash: str) -> None:
        """Mark a token as used (for rotation)."""
        pass

    @abstractmethod
    async def update_last_used(self, token_hash: str) -> None:
        """Update last_used_at timestamp for sliding window."""
        pass

    @abstractmethod
    async def revoke(self, token_hash: str) -> None:
        """Revoke a single token."""
        pass

    @abstractmethod
    async def revoke_family(self, family_id: str) -> int:
        """
        Revoke all tokens in a family (theft detection response).

        Returns:
            Number of tokens revoked
        """
        pass

    @abstractmethod
    async def revoke_all(self, user_id: str) -> int:
        """
        Revoke all tokens for a user (logout from all devices).

        Returns:
            Number of tokens revoked
        """
        pass

    @abstractmethod
    async def cleanup_expired(self) -> int:
        """
        Remove all expired tokens.

        Returns:
            Number of tokens removed
        """
        pass

    async def rotate(
        self,
        old_token: str,
        user_id: str,
        family_id: str,
    ) -> tuple[str, RefreshToken]:
        """
        Rotate a refresh token.

        1. Mark old token as used
        2. Issue new token in same family

        Returns:
            Tuple of (new_raw_token, RefreshToken)
        """
        old_hash = hash_token(old_token)
        await self.mark_used(old_hash)

        new_token = generate_token()
        token_data = await self.store(user_id, new_token, family_id)

        return new_token, token_data


class InMemoryTokenStore(TokenStoreBase):
    """
    In-memory token store for development.

    Uses a dict keyed by token_hash.
    """

    def __init__(self) -> None:
        self._tokens: Dict[str, RefreshToken] = {}
        # Secondary indices for efficient lookups
        self._by_family: Dict[str, List[str]] = {}  # family_id -> [token_hash]
        self._by_user: Dict[str, List[str]] = {}  # user_id -> [token_hash]

    async def store(
        self,
        user_id: str,
        token: str,
        family_id: str,
    ) -> RefreshToken:
        token_hash = hash_token(token)
        now = datetime.now(timezone.utc)

        token_data = RefreshToken(
            token_hash=token_hash,
            user_id=user_id,
            family_id=family_id,
            issued_at=now,
            expires_at=now + timedelta(days=ABSOLUTE_EXPIRY_DAYS),
            last_used_at=now,
            used=False,
        )

        self._tokens[token_hash] = token_data

        # Update indices
        if family_id not in self._by_family:
            self._by_family[family_id] = []
        self._by_family[family_id].append(token_hash)

        if user_id not in self._by_user:
            self._by_user[user_id] = []
        self._by_user[user_id].append(token_hash)

        logger.debug(f"Stored token for user {user_id} in family {family_id}")
        return token_data

    async def validate(self, token: str) -> TokenValidationResult:
        token_hash = hash_token(token)
        token_data = self._tokens.get(token_hash)

        if token_data is None:
            return TokenValidationResult(is_valid=False)

        now = datetime.now(timezone.utc)

        # Check absolute expiry
        if now >= token_data.expires_at:
            logger.debug(f"Token {token_hash[:8]}... expired (absolute)")
            return TokenValidationResult(is_valid=False)

        # Check sliding window
        sliding_expiry = token_data.last_used_at + timedelta(days=SLIDING_WINDOW_DAYS)
        if now >= sliding_expiry:
            logger.debug(f"Token {token_hash[:8]}... expired (sliding window)")
            return TokenValidationResult(is_valid=False)

        return TokenValidationResult(
            is_valid=True,
            is_used=token_data.used,
            family_id=token_data.family_id,
            user_id=token_data.user_id,
            token_hash=token_hash,
        )

    async def mark_used(self, token_hash: str) -> None:
        if token_hash in self._tokens:
            self._tokens[token_hash].used = True
            logger.debug(f"Marked token {token_hash[:8]}... as used")

    async def update_last_used(self, token_hash: str) -> None:
        if token_hash in self._tokens:
            self._tokens[token_hash].last_used_at = datetime.now(timezone.utc)

    async def revoke(self, token_hash: str) -> None:
        token_data = self._tokens.pop(token_hash, None)
        if token_data:
            # Clean up indices
            if token_data.family_id in self._by_family:
                self._by_family[token_data.family_id] = [
                    h for h in self._by_family[token_data.family_id] if h != token_hash
                ]
            if token_data.user_id in self._by_user:
                self._by_user[token_data.user_id] = [
                    h for h in self._by_user[token_data.user_id] if h != token_hash
                ]
            logger.info(f"Revoked token {token_hash[:8]}...")

    async def revoke_family(self, family_id: str) -> int:
        token_hashes = self._by_family.pop(family_id, [])
        count = 0
        for token_hash in token_hashes:
            token_data = self._tokens.pop(token_hash, None)
            if token_data:
                count += 1
                # Clean up user index
                if token_data.user_id in self._by_user:
                    self._by_user[token_data.user_id] = [
                        h for h in self._by_user[token_data.user_id] if h != token_hash
                    ]
        logger.warning(f"Revoked {count} tokens in family {family_id} (potential theft)")
        return count

    async def revoke_all(self, user_id: str) -> int:
        token_hashes = self._by_user.pop(user_id, [])
        count = 0
        for token_hash in token_hashes:
            token_data = self._tokens.pop(token_hash, None)
            if token_data:
                count += 1
                # Clean up family index
                if token_data.family_id in self._by_family:
                    self._by_family[token_data.family_id] = [
                        h for h in self._by_family[token_data.family_id] if h != token_hash
                    ]
        logger.info(f"Revoked {count} tokens for user {user_id}")
        return count

    async def cleanup_expired(self) -> int:
        now = datetime.now(timezone.utc)
        expired = []

        for token_hash, token_data in self._tokens.items():
            # Check absolute expiry
            if now >= token_data.expires_at:
                expired.append(token_hash)
                continue

            # Check sliding window
            sliding_expiry = token_data.last_used_at + timedelta(days=SLIDING_WINDOW_DAYS)
            if now >= sliding_expiry:
                expired.append(token_hash)

        for token_hash in expired:
            await self.revoke(token_hash)

        return len(expired)


class RedisTokenStore(TokenStoreBase):
    """
    Redis-backed token store for production.

    Uses Redis hashes for token data and sets for indices.
    """

    def __init__(self, redis_url: str = "redis://localhost:6379") -> None:
        self._redis_url = redis_url
        self._redis: Any = None

    async def _get_redis(self) -> Any:
        """Lazy Redis connection initialization."""
        if self._redis is None:
            try:
                import redis.asyncio as aioredis
                self._redis = await aioredis.from_url(
                    self._redis_url,
                    encoding="utf-8",
                    decode_responses=True,
                )
            except ImportError:
                raise RuntimeError("redis package required for production mode")
        return self._redis

    def _token_key(self, token_hash: str) -> str:
        return f"refresh_token:{token_hash}"

    def _family_key(self, family_id: str) -> str:
        return f"token_family:{family_id}"

    def _user_key(self, user_id: str) -> str:
        return f"user_tokens:{user_id}"

    async def store(
        self,
        user_id: str,
        token: str,
        family_id: str,
    ) -> RefreshToken:
        redis = await self._get_redis()
        token_hash = hash_token(token)
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(days=ABSOLUTE_EXPIRY_DAYS)

        token_data = RefreshToken(
            token_hash=token_hash,
            user_id=user_id,
            family_id=family_id,
            issued_at=now,
            expires_at=expires_at,
            last_used_at=now,
            used=False,
        )

        # Store token data as hash
        token_key = self._token_key(token_hash)
        await redis.hset(token_key, mapping={
            "user_id": user_id,
            "family_id": family_id,
            "issued_at": now.isoformat(),
            "expires_at": expires_at.isoformat(),
            "last_used_at": now.isoformat(),
            "used": "0",
        })
        # Set TTL slightly beyond absolute expiry for cleanup
        await redis.expire(token_key, ABSOLUTE_EXPIRY_DAYS * 86400 + 3600)

        # Add to indices (sets with TTL)
        await redis.sadd(self._family_key(family_id), token_hash)
        await redis.expire(self._family_key(family_id), ABSOLUTE_EXPIRY_DAYS * 86400 + 3600)

        await redis.sadd(self._user_key(user_id), token_hash)
        await redis.expire(self._user_key(user_id), ABSOLUTE_EXPIRY_DAYS * 86400 + 3600)

        logger.debug(f"Stored token for user {user_id} in family {family_id}")
        return token_data

    async def validate(self, token: str) -> TokenValidationResult:
        redis = await self._get_redis()
        token_hash = hash_token(token)
        token_key = self._token_key(token_hash)

        data = await redis.hgetall(token_key)
        if not data:
            return TokenValidationResult(is_valid=False)

        now = datetime.now(timezone.utc)

        # Parse stored data
        expires_at = datetime.fromisoformat(data["expires_at"])
        last_used_at = datetime.fromisoformat(data["last_used_at"])
        used = data.get("used", "0") == "1"

        # Check absolute expiry
        if now >= expires_at:
            return TokenValidationResult(is_valid=False)

        # Check sliding window
        sliding_expiry = last_used_at + timedelta(days=SLIDING_WINDOW_DAYS)
        if now >= sliding_expiry:
            return TokenValidationResult(is_valid=False)

        return TokenValidationResult(
            is_valid=True,
            is_used=used,
            family_id=data["family_id"],
            user_id=data["user_id"],
            token_hash=token_hash,
        )

    async def mark_used(self, token_hash: str) -> None:
        redis = await self._get_redis()
        await redis.hset(self._token_key(token_hash), "used", "1")
        logger.debug(f"Marked token {token_hash[:8]}... as used")

    async def update_last_used(self, token_hash: str) -> None:
        redis = await self._get_redis()
        await redis.hset(
            self._token_key(token_hash),
            "last_used_at",
            datetime.now(timezone.utc).isoformat(),
        )

    async def revoke(self, token_hash: str) -> None:
        redis = await self._get_redis()
        token_key = self._token_key(token_hash)

        # Get token data for index cleanup
        data = await redis.hgetall(token_key)
        if data:
            family_id = data.get("family_id")
            user_id = data.get("user_id")

            # Remove from indices
            if family_id:
                await redis.srem(self._family_key(family_id), token_hash)
            if user_id:
                await redis.srem(self._user_key(user_id), token_hash)

        await redis.delete(token_key)
        logger.info(f"Revoked token {token_hash[:8]}...")

    async def revoke_family(self, family_id: str) -> int:
        redis = await self._get_redis()
        family_key = self._family_key(family_id)

        token_hashes = await redis.smembers(family_key)
        count = 0

        for token_hash in token_hashes:
            token_key = self._token_key(token_hash)
            data = await redis.hgetall(token_key)
            if data:
                user_id = data.get("user_id")
                if user_id:
                    await redis.srem(self._user_key(user_id), token_hash)
                await redis.delete(token_key)
                count += 1

        await redis.delete(family_key)
        logger.warning(f"Revoked {count} tokens in family {family_id} (potential theft)")
        return count

    async def revoke_all(self, user_id: str) -> int:
        redis = await self._get_redis()
        user_key = self._user_key(user_id)

        token_hashes = await redis.smembers(user_key)
        count = 0

        for token_hash in token_hashes:
            token_key = self._token_key(token_hash)
            data = await redis.hgetall(token_key)
            if data:
                family_id = data.get("family_id")
                if family_id:
                    await redis.srem(self._family_key(family_id), token_hash)
                await redis.delete(token_key)
                count += 1

        await redis.delete(user_key)
        logger.info(f"Revoked {count} tokens for user {user_id}")
        return count

    async def cleanup_expired(self) -> int:
        # Redis TTL handles expiration automatically
        # This method is for manual cleanup if needed
        return 0

    async def close(self) -> None:
        """Close Redis connection."""
        if self._redis:
            await self._redis.close()


def get_token_store() -> TokenStoreBase:
    """
    Factory function to get the appropriate token store.

    Returns InMemoryTokenStore for development, RedisTokenStore for production.
    """
    app_env = os.getenv("APP_ENV", "development")

    if app_env == "production":
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        return RedisTokenStore(redis_url)

    return InMemoryTokenStore()


# Module-level singleton
_token_store: Optional[TokenStoreBase] = None


def get_token_store_instance() -> TokenStoreBase:
    """Get or create the singleton token store instance."""
    global _token_store
    if _token_store is None:
        _token_store = get_token_store()
    return _token_store

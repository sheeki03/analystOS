"""
Rate Limiter Service

Sliding window rate limiter with:
- Authenticated users: 100 req/min keyed by user_id
- Unauthenticated: 30 req/min keyed by IP

Production: Redis ZSET for distributed rate limiting
Development: In-memory dict for simplicity

Returns 429 Too Many Requests with Retry-After header when limit exceeded.
"""

import asyncio
import logging
import os
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from fastapi import Request

logger = logging.getLogger(__name__)


# Rate limit configurations from plan
AUTHENTICATED_LIMIT = 100  # requests per minute
AUTHENTICATED_WINDOW = 60  # seconds

UNAUTHENTICATED_LIMIT = 30  # requests per minute
UNAUTHENTICATED_WINDOW = 60  # seconds


@dataclass
class RateLimitResult:
    """Result of rate limit check."""
    allowed: bool
    remaining: int
    limit: int
    reset_after: float  # seconds until window resets
    retry_after: Optional[float] = None  # seconds to wait if blocked


class RateLimiterBase(ABC):
    """Abstract base class for rate limiters."""

    @abstractmethod
    async def check(
        self,
        key: str,
        limit: int,
        window_seconds: int,
    ) -> RateLimitResult:
        """
        Check if request is allowed under rate limit.

        Uses sliding window algorithm:
        - Count requests in the past window_seconds
        - Allow if count < limit

        Args:
            key: Rate limit key (user_id or IP)
            limit: Maximum requests allowed
            window_seconds: Time window in seconds

        Returns:
            RateLimitResult with allowed status and metadata
        """
        pass

    @abstractmethod
    async def reset(self, key: str) -> None:
        """Reset rate limit for a key."""
        pass


class InMemoryRateLimiter(RateLimiterBase):
    """
    In-memory sliding window rate limiter for development.

    Stores timestamps of requests per key.
    """

    def __init__(self) -> None:
        self._requests: Dict[str, List[float]] = {}
        self._lock = asyncio.Lock()

    async def check(
        self,
        key: str,
        limit: int,
        window_seconds: int,
    ) -> RateLimitResult:
        async with self._lock:
            now = time.time()
            window_start = now - window_seconds

            # Get existing timestamps, filter to window
            timestamps = self._requests.get(key, [])
            timestamps = [t for t in timestamps if t > window_start]

            current_count = len(timestamps)

            if current_count >= limit:
                # Rate limited - calculate retry after
                oldest_in_window = min(timestamps) if timestamps else now
                retry_after = oldest_in_window + window_seconds - now

                return RateLimitResult(
                    allowed=False,
                    remaining=0,
                    limit=limit,
                    reset_after=retry_after,
                    retry_after=max(0, retry_after),
                )

            # Add current request
            timestamps.append(now)
            self._requests[key] = timestamps

            # Calculate reset time (when oldest request exits window)
            oldest_in_window = min(timestamps) if timestamps else now
            reset_after = oldest_in_window + window_seconds - now

            return RateLimitResult(
                allowed=True,
                remaining=limit - len(timestamps),
                limit=limit,
                reset_after=reset_after,
            )

    async def reset(self, key: str) -> None:
        async with self._lock:
            self._requests.pop(key, None)

    async def cleanup(self, max_age_seconds: int = 300) -> int:
        """Remove stale entries older than max_age_seconds."""
        async with self._lock:
            now = time.time()
            cutoff = now - max_age_seconds

            stale_keys = []
            for key, timestamps in self._requests.items():
                # Remove old timestamps
                self._requests[key] = [t for t in timestamps if t > cutoff]
                # Mark for removal if empty
                if not self._requests[key]:
                    stale_keys.append(key)

            for key in stale_keys:
                del self._requests[key]

            return len(stale_keys)


class RedisRateLimiter(RateLimiterBase):
    """
    Redis-backed sliding window rate limiter for production.

    Uses sorted sets (ZSET) with timestamp scores for efficient sliding window.
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

    def _rate_key(self, key: str) -> str:
        return f"ratelimit:{key}"

    async def check(
        self,
        key: str,
        limit: int,
        window_seconds: int,
    ) -> RateLimitResult:
        redis = await self._get_redis()
        rate_key = self._rate_key(key)
        now = time.time()
        window_start = now - window_seconds

        # Use pipeline for atomic operations
        pipe = redis.pipeline()

        # Remove old entries outside window
        pipe.zremrangebyscore(rate_key, "-inf", window_start)

        # Count current entries
        pipe.zcard(rate_key)

        # Get oldest entry for reset time calculation
        pipe.zrange(rate_key, 0, 0, withscores=True)

        results = await pipe.execute()
        current_count = results[1]
        oldest_entries = results[2]

        if current_count >= limit:
            # Rate limited
            oldest_timestamp = oldest_entries[0][1] if oldest_entries else now
            retry_after = oldest_timestamp + window_seconds - now

            return RateLimitResult(
                allowed=False,
                remaining=0,
                limit=limit,
                reset_after=max(0, retry_after),
                retry_after=max(0, retry_after),
            )

        # Add current request
        await redis.zadd(rate_key, {str(now): now})
        # Set TTL on the key
        await redis.expire(rate_key, window_seconds + 1)

        # Recalculate remaining
        new_count = current_count + 1
        oldest_timestamp = oldest_entries[0][1] if oldest_entries else now
        reset_after = oldest_timestamp + window_seconds - now

        return RateLimitResult(
            allowed=True,
            remaining=limit - new_count,
            limit=limit,
            reset_after=max(0, reset_after),
        )

    async def reset(self, key: str) -> None:
        redis = await self._get_redis()
        await redis.delete(self._rate_key(key))

    async def close(self) -> None:
        """Close Redis connection."""
        if self._redis:
            await self._redis.close()


def get_rate_limiter() -> RateLimiterBase:
    """
    Factory function to get the appropriate rate limiter.

    Returns InMemoryRateLimiter for development, RedisRateLimiter for production.
    """
    app_env = os.getenv("APP_ENV", "development")

    if app_env == "production":
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        return RedisRateLimiter(redis_url)

    return InMemoryRateLimiter()


# Module-level singleton
_rate_limiter: Optional[RateLimiterBase] = None


def get_rate_limiter_instance() -> RateLimiterBase:
    """Get or create the singleton rate limiter instance."""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = get_rate_limiter()
    return _rate_limiter


def get_client_ip(request: Request) -> str:
    """
    Extract client IP from request with proxy awareness.

    In production behind a proxy:
    - Use X-Forwarded-For header if trusted
    - TRUSTED_PROXIES env var contains comma-separated trusted proxy IPs

    In development or without proxy:
    - Use request.client.host directly
    """
    trusted_proxies_str = os.getenv("TRUSTED_PROXIES", "")
    trusted_proxies = set(
        ip.strip() for ip in trusted_proxies_str.split(",") if ip.strip()
    )

    # If we have trusted proxies configured, try X-Forwarded-For
    if trusted_proxies and request.client:
        client_ip = request.client.host

        if client_ip in trusted_proxies:
            # Request is from a trusted proxy, use X-Forwarded-For
            forwarded_for = request.headers.get("X-Forwarded-For")
            if forwarded_for:
                # X-Forwarded-For can contain multiple IPs: "client, proxy1, proxy2"
                # The first non-trusted IP is the real client
                ips = [ip.strip() for ip in forwarded_for.split(",")]
                for ip in ips:
                    if ip not in trusted_proxies:
                        return ip
                # All IPs are trusted proxies, use the first one
                return ips[0] if ips else client_ip

    # No trusted proxies or request not from proxy
    if request.client:
        return request.client.host

    return "unknown"


def get_rate_limit_key(request: Request, user_id: Optional[str] = None) -> str:
    """
    Get the rate limit key for a request.

    Authenticated users are keyed by user_id.
    Unauthenticated requests are keyed by IP.
    """
    if user_id:
        return f"user:{user_id}"
    return f"ip:{get_client_ip(request)}"


def get_rate_limit_config(user_id: Optional[str] = None) -> Tuple[int, int]:
    """
    Get rate limit configuration based on auth status.

    Returns:
        Tuple of (limit, window_seconds)
    """
    if user_id:
        return AUTHENTICATED_LIMIT, AUTHENTICATED_WINDOW
    return UNAUTHENTICATED_LIMIT, UNAUTHENTICATED_WINDOW

"""
Cache Service

Provides a unified caching interface with:
- TTL (Time To Live) support
- Stale-while-error: Serve stale data when upstream fails
- X-Cache header support (HIT/MISS/STALE)

Production: Redis backend
Development: In-memory dict with TTL tracking
"""

import asyncio
import json
import logging
import os
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Generic, Optional, Tuple, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


class CacheStatus(str, Enum):
    HIT = "HIT"
    MISS = "MISS"
    STALE = "STALE"


@dataclass
class CacheEntry(Generic[T]):
    """Cache entry with value and timing metadata."""
    value: T
    created_at: float
    ttl: float
    max_stale: float = 0

    @property
    def expires_at(self) -> float:
        return self.created_at + self.ttl

    @property
    def stale_until(self) -> float:
        return self.expires_at + self.max_stale

    def is_fresh(self) -> bool:
        return time.time() < self.expires_at

    def is_stale_valid(self) -> bool:
        """Check if stale data can still be served."""
        now = time.time()
        return self.expires_at <= now < self.stale_until


class CacheServiceBase(ABC):
    """Abstract base class for cache services."""

    @abstractmethod
    async def get(self, key: str) -> Tuple[Optional[Any], CacheStatus]:
        """
        Get cached value.

        Returns:
            Tuple of (value or None, cache_status)
            - (value, HIT) if fresh data exists
            - (value, STALE) if only stale data exists
            - (None, MISS) if no data exists
        """
        pass

    @abstractmethod
    async def set(
        self,
        key: str,
        value: Any,
        ttl: float,
        max_stale: float = 0,
    ) -> None:
        """
        Set cached value with TTL and optional max_stale window.

        Args:
            key: Cache key
            value: Value to cache (must be JSON serializable)
            ttl: Time to live in seconds
            max_stale: Additional seconds to serve stale data on upstream failure
        """
        pass

    @abstractmethod
    async def delete(self, key: str) -> None:
        """Delete a cached value."""
        pass

    @abstractmethod
    async def clear(self) -> None:
        """Clear all cached values."""
        pass

    async def get_or_set(
        self,
        key: str,
        fetch_func: Any,
        ttl: float,
        max_stale: float = 0,
    ) -> Tuple[Any, CacheStatus]:
        """
        Get from cache, or fetch and cache if missing.

        Implements stale-while-error: If fresh data fetch fails but stale
        data exists, return the stale data.

        Args:
            key: Cache key
            fetch_func: Async function to fetch fresh data
            ttl: TTL for fresh data
            max_stale: Max age for stale data to be served on error

        Returns:
            Tuple of (value, cache_status)
        """
        # Try to get from cache
        value, status = await self.get(key)

        if status == CacheStatus.HIT:
            return value, status

        # Cache miss or stale - try to fetch fresh data
        try:
            fresh_value = await fetch_func()
            await self.set(key, fresh_value, ttl, max_stale)
            return fresh_value, CacheStatus.MISS
        except Exception as e:
            logger.warning(f"Failed to fetch fresh data for {key}: {e}")

            # If we have stale data, return it
            if status == CacheStatus.STALE and value is not None:
                logger.info(f"Serving stale data for {key}")
                return value, CacheStatus.STALE

            # No stale data available, re-raise the exception
            raise


class InMemoryCacheService(CacheServiceBase):
    """
    In-memory cache for development.

    Uses a dict with CacheEntry objects for TTL tracking.
    Thread-safe via asyncio locks.
    """

    def __init__(self) -> None:
        self._cache: Dict[str, CacheEntry[Any]] = {}
        self._lock = asyncio.Lock()

    async def get(self, key: str) -> Tuple[Optional[Any], CacheStatus]:
        async with self._lock:
            entry = self._cache.get(key)

            if entry is None:
                return None, CacheStatus.MISS

            if entry.is_fresh():
                return entry.value, CacheStatus.HIT

            if entry.is_stale_valid():
                return entry.value, CacheStatus.STALE

            # Entry is completely expired
            del self._cache[key]
            return None, CacheStatus.MISS

    async def set(
        self,
        key: str,
        value: Any,
        ttl: float,
        max_stale: float = 0,
    ) -> None:
        async with self._lock:
            self._cache[key] = CacheEntry(
                value=value,
                created_at=time.time(),
                ttl=ttl,
                max_stale=max_stale,
            )

    async def delete(self, key: str) -> None:
        async with self._lock:
            self._cache.pop(key, None)

    async def clear(self) -> None:
        async with self._lock:
            self._cache.clear()

    async def cleanup_expired(self) -> int:
        """Remove all expired entries. Returns count of removed entries."""
        async with self._lock:
            now = time.time()
            expired = [
                key for key, entry in self._cache.items()
                if now >= entry.stale_until
            ]
            for key in expired:
                del self._cache[key]
            return len(expired)


class RedisCacheService(CacheServiceBase):
    """
    Redis-backed cache for production.

    Stores values as JSON with metadata for stale-while-error support.
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

    def _cache_key(self, key: str) -> str:
        return f"cache:{key}"

    async def get(self, key: str) -> Tuple[Optional[Any], CacheStatus]:
        redis = await self._get_redis()
        cache_key = self._cache_key(key)

        data = await redis.get(cache_key)
        if data is None:
            return None, CacheStatus.MISS

        try:
            entry = json.loads(data)
            value = entry["value"]
            created_at = entry["created_at"]
            ttl = entry["ttl"]
            max_stale = entry.get("max_stale", 0)

            now = time.time()
            expires_at = created_at + ttl
            stale_until = expires_at + max_stale

            if now < expires_at:
                return value, CacheStatus.HIT

            if now < stale_until:
                return value, CacheStatus.STALE

            # Completely expired - delete and return miss
            await redis.delete(cache_key)
            return None, CacheStatus.MISS

        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(f"Invalid cache entry for {key}: {e}")
            await redis.delete(cache_key)
            return None, CacheStatus.MISS

    async def set(
        self,
        key: str,
        value: Any,
        ttl: float,
        max_stale: float = 0,
    ) -> None:
        redis = await self._get_redis()
        cache_key = self._cache_key(key)

        entry = {
            "value": value,
            "created_at": time.time(),
            "ttl": ttl,
            "max_stale": max_stale,
        }

        # Redis TTL includes both fresh TTL and max_stale window
        redis_ttl = int(ttl + max_stale) + 1  # +1 for safety margin

        await redis.setex(
            cache_key,
            redis_ttl,
            json.dumps(entry),
        )

    async def delete(self, key: str) -> None:
        redis = await self._get_redis()
        await redis.delete(self._cache_key(key))

    async def clear(self) -> None:
        redis = await self._get_redis()
        # Use SCAN to find all cache keys and delete them
        cursor = 0
        while True:
            cursor, keys = await redis.scan(cursor, match="cache:*", count=100)
            if keys:
                await redis.delete(*keys)
            if cursor == 0:
                break

    async def close(self) -> None:
        """Close Redis connection."""
        if self._redis:
            await self._redis.close()


def get_cache_service() -> CacheServiceBase:
    """
    Factory function to get the appropriate cache service.

    Returns InMemoryCacheService for development, RedisCacheService for production.
    """
    app_env = os.getenv("APP_ENV", "development")

    if app_env == "production":
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        return RedisCacheService(redis_url)

    return InMemoryCacheService()


# Module-level singleton
_cache_service: Optional[CacheServiceBase] = None


def get_cache_service_instance() -> CacheServiceBase:
    """Get or create the singleton cache service instance."""
    global _cache_service
    if _cache_service is None:
        _cache_service = get_cache_service()
    return _cache_service


# Predefined cache configurations for different endpoint types
class CacheConfig:
    """Cache configuration presets matching the API plan."""

    # Crypto endpoints
    PRICE = {"ttl": 30, "max_stale": 300}  # 30s fresh, 5m stale
    TRENDING = {"ttl": 60, "max_stale": 600}  # 60s fresh, 10m stale
    SEARCH = {"ttl": 300, "max_stale": 1800}  # 5m fresh, 30m stale
    MARKET_OVERVIEW = {"ttl": 60, "max_stale": 600}  # 60s fresh, 10m stale
    HISTORICAL = {"ttl": 300, "max_stale": 3600}  # 5m fresh, 1h stale

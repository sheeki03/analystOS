"""
Crypto Router

Cached and rate-limited cryptocurrency endpoints:
- GET /crypto/price/{coin_id} - Current price (30s cache, 5m stale)
- GET /crypto/trending - Trending coins (60s cache, 10m stale)
- GET /crypto/search - Search coins (5m cache, 30m stale)
- GET /crypto/market-overview - Market overview (60s cache, 10m stale)
- GET /crypto/historical/{coin_id} - Historical data (5m cache, 1h stale)
- POST /crypto/chat - AI chat (no cache)

All endpoints use:
- Caching with stale-while-error for resilience
- Rate limiting (100/min auth, 30/min unauth)
- X-Cache header to indicate cache status
"""

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from pydantic import BaseModel

from src.models.auth_models import TokenPayload
from src.routers.auth_router import get_current_user, get_current_user_optional
from src.services.cache_service import (
    CacheConfig,
    CacheServiceBase,
    CacheStatus,
    get_cache_service_instance,
)
from src.services.rate_limiter import (
    RateLimitResult,
    RateLimiterBase,
    get_rate_limit_config,
    get_rate_limit_key,
    get_rate_limiter_instance,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/crypto", tags=["Crypto"])


# ============================================================================
# Models
# ============================================================================

class PriceResponse(BaseModel):
    """Coin price response."""
    coin_id: str
    name: str
    symbol: str
    current_price: float
    price_change_24h: float
    price_change_percentage_24h: float
    market_cap: float
    volume_24h: float
    last_updated: str


class TrendingCoin(BaseModel):
    """Trending coin info."""
    coin_id: str
    name: str
    symbol: str
    market_cap_rank: Optional[int] = None
    price_btc: float
    score: int


class TrendingResponse(BaseModel):
    """Trending coins response."""
    coins: List[TrendingCoin]


class SearchResult(BaseModel):
    """Search result item."""
    coin_id: str
    name: str
    symbol: str
    market_cap_rank: Optional[int] = None
    thumb: Optional[str] = None


class SearchResponse(BaseModel):
    """Search response."""
    coins: List[SearchResult]


class MarketOverviewResponse(BaseModel):
    """Market overview response."""
    total_market_cap: float
    total_volume_24h: float
    btc_dominance: float
    eth_dominance: float
    active_cryptocurrencies: int
    markets: int
    market_cap_change_24h: float


class HistoricalDataPoint(BaseModel):
    """Single historical data point."""
    timestamp: int
    price: float
    volume: Optional[float] = None
    market_cap: Optional[float] = None


class HistoricalResponse(BaseModel):
    """Historical price data response."""
    coin_id: str
    prices: List[HistoricalDataPoint]
    days: int


class ChatMessage(BaseModel):
    """Chat message."""
    role: str  # "user" or "assistant"
    content: str


class ChatRequest(BaseModel):
    """Chat request."""
    message: str
    history: List[ChatMessage] = []
    context: Optional[Dict[str, Any]] = None


class ChatResponse(BaseModel):
    """Chat response."""
    message: str
    context: Optional[Dict[str, Any]] = None


# ============================================================================
# Dependencies
# ============================================================================

def get_cache() -> CacheServiceBase:
    """Dependency to get cache service."""
    return get_cache_service_instance()


def get_rate_limiter() -> RateLimiterBase:
    """Dependency to get rate limiter."""
    return get_rate_limiter_instance()


async def check_rate_limit(
    request: Request,
    current_user: Optional[TokenPayload] = Depends(get_current_user_optional),
    rate_limiter: RateLimiterBase = Depends(get_rate_limiter),
) -> RateLimitResult:
    """
    Dependency to check and enforce rate limits.

    Raises 429 if rate limit exceeded.
    """
    user_id = current_user.sub if current_user else None
    key = get_rate_limit_key(request, user_id)
    limit, window = get_rate_limit_config(user_id)

    result = await rate_limiter.check(key, limit, window)

    if not result.allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded",
            headers={"Retry-After": str(int(result.retry_after or 60))},
        )

    return result


def set_cache_header(response: Response, status: CacheStatus) -> None:
    """Set X-Cache header on response."""
    response.headers["X-Cache"] = status.value


# ============================================================================
# CoinGecko Integration (placeholder - uses existing mcp/coingecko_client.py)
# ============================================================================

async def fetch_coin_price(coin_id: str) -> Dict[str, Any]:
    """Fetch current price from CoinGecko."""
    # TODO: Use existing coingecko_client.py
    # Placeholder response
    return {
        "coin_id": coin_id,
        "name": coin_id.title(),
        "symbol": coin_id[:3].upper(),
        "current_price": 50000.0,
        "price_change_24h": 1000.0,
        "price_change_percentage_24h": 2.0,
        "market_cap": 1000000000000,
        "volume_24h": 50000000000,
        "last_updated": "2024-01-01T00:00:00Z",
    }


async def fetch_trending() -> Dict[str, Any]:
    """Fetch trending coins from CoinGecko."""
    # TODO: Use existing coingecko_client.py
    return {
        "coins": [
            {
                "coin_id": "bitcoin",
                "name": "Bitcoin",
                "symbol": "BTC",
                "market_cap_rank": 1,
                "price_btc": 1.0,
                "score": 0,
            },
        ],
    }


async def fetch_search(query: str) -> Dict[str, Any]:
    """Search coins on CoinGecko."""
    # TODO: Use existing coingecko_client.py
    return {
        "coins": [
            {
                "coin_id": "bitcoin",
                "name": "Bitcoin",
                "symbol": "BTC",
                "market_cap_rank": 1,
            },
        ],
    }


async def fetch_market_overview() -> Dict[str, Any]:
    """Fetch market overview from CoinGecko."""
    # TODO: Use existing coingecko_client.py
    return {
        "total_market_cap": 2000000000000,
        "total_volume_24h": 100000000000,
        "btc_dominance": 45.0,
        "eth_dominance": 18.0,
        "active_cryptocurrencies": 10000,
        "markets": 800,
        "market_cap_change_24h": 2.5,
    }


async def fetch_historical(coin_id: str, days: int) -> Dict[str, Any]:
    """Fetch historical price data from CoinGecko."""
    # TODO: Use existing coingecko_client.py
    return {
        "coin_id": coin_id,
        "prices": [
            {"timestamp": 1704067200000, "price": 45000.0},
            {"timestamp": 1704153600000, "price": 46000.0},
        ],
        "days": days,
    }


# ============================================================================
# Endpoints
# ============================================================================

@router.get("/price/{coin_id}", response_model=PriceResponse)
async def get_price(
    coin_id: str,
    response: Response,
    _rate_limit: RateLimitResult = Depends(check_rate_limit),
    cache: CacheServiceBase = Depends(get_cache),
) -> PriceResponse:
    """
    Get current price for a coin.

    Cache: 30s fresh, 5m stale
    """
    cache_key = f"crypto:price:{coin_id}"

    data, cache_status = await cache.get_or_set(
        key=cache_key,
        fetch_func=lambda: fetch_coin_price(coin_id),
        **CacheConfig.PRICE,
    )

    set_cache_header(response, cache_status)

    return PriceResponse(**data)


@router.get("/trending", response_model=TrendingResponse)
async def get_trending(
    response: Response,
    _rate_limit: RateLimitResult = Depends(check_rate_limit),
    cache: CacheServiceBase = Depends(get_cache),
) -> TrendingResponse:
    """
    Get trending coins.

    Cache: 60s fresh, 10m stale
    """
    cache_key = "crypto:trending"

    data, cache_status = await cache.get_or_set(
        key=cache_key,
        fetch_func=fetch_trending,
        **CacheConfig.TRENDING,
    )

    set_cache_header(response, cache_status)

    return TrendingResponse(**data)


@router.get("/search", response_model=SearchResponse)
async def search_coins(
    q: str = Query(..., min_length=1, description="Search query"),
    response: Response = None,
    _rate_limit: RateLimitResult = Depends(check_rate_limit),
    cache: CacheServiceBase = Depends(get_cache),
) -> SearchResponse:
    """
    Search for coins.

    Cache: 5m fresh, 30m stale
    """
    cache_key = f"crypto:search:{q.lower()}"

    data, cache_status = await cache.get_or_set(
        key=cache_key,
        fetch_func=lambda: fetch_search(q),
        **CacheConfig.SEARCH,
    )

    set_cache_header(response, cache_status)

    return SearchResponse(**data)


@router.get("/market-overview", response_model=MarketOverviewResponse)
async def get_market_overview(
    response: Response,
    _rate_limit: RateLimitResult = Depends(check_rate_limit),
    cache: CacheServiceBase = Depends(get_cache),
) -> MarketOverviewResponse:
    """
    Get market overview stats.

    Cache: 60s fresh, 10m stale
    """
    cache_key = "crypto:market-overview"

    data, cache_status = await cache.get_or_set(
        key=cache_key,
        fetch_func=fetch_market_overview,
        **CacheConfig.MARKET_OVERVIEW,
    )

    set_cache_header(response, cache_status)

    return MarketOverviewResponse(**data)


@router.get("/historical/{coin_id}", response_model=HistoricalResponse)
async def get_historical(
    coin_id: str,
    days: int = Query(7, ge=1, le=365, description="Number of days"),
    response: Response = None,
    _rate_limit: RateLimitResult = Depends(check_rate_limit),
    cache: CacheServiceBase = Depends(get_cache),
) -> HistoricalResponse:
    """
    Get historical price data.

    Cache: 5m fresh, 1h stale
    """
    cache_key = f"crypto:historical:{coin_id}:{days}"

    data, cache_status = await cache.get_or_set(
        key=cache_key,
        fetch_func=lambda: fetch_historical(coin_id, days),
        **CacheConfig.HISTORICAL,
    )

    set_cache_header(response, cache_status)

    return HistoricalResponse(**data)


@router.post("/chat", response_model=ChatResponse)
async def crypto_chat(
    request: ChatRequest,
    current_user: TokenPayload = Depends(get_current_user),
    _rate_limit: RateLimitResult = Depends(check_rate_limit),
) -> ChatResponse:
    """
    AI chat about cryptocurrency.

    No caching - real-time responses.
    Requires authentication.
    """
    # TODO: Integrate with existing crypto chatbot
    # Placeholder response
    return ChatResponse(
        message=f"I understand you're asking about: {request.message}. "
        f"This is a placeholder response. Real implementation will use the AI model.",
        context=request.context,
    )

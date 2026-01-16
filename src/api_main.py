"""
analystOS API - FastAPI Application

Main entry point for the REST API.

Run with:
  Development: uvicorn src.api_main:app --reload --port 8000
  Production: uvicorn src.api_main:app --host 0.0.0.0 --port 8000

API Structure:
  /auth/*       - Authentication (login, refresh, logout, me)
  /research/*   - Research operations (upload, scrape, generate, jobs, reports)
  /crypto/*     - Cryptocurrency data (prices, trending, search, chat)
  /automation/* - Notion automation (status, queue, trigger, history)
  /chat/*       - Existing chat functionality (preserved)

Middleware Stack (order matters):
  1. LimitUploadSizeMiddleware (first - reject large uploads early)
  2. CORSMiddleware
"""

import logging
import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.services.upload_middleware import LimitUploadSizeMiddleware

# Import routers
from src.routers.auth_router import router as auth_router
from src.routers.research_router import router as research_router
from src.routers.crypto_router import router as crypto_router
from src.routers.automation_router import router as automation_router
from src.routers.chat_router import router as chat_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Environment
APP_ENV = os.getenv("APP_ENV", "development")
DEBUG = os.getenv("DEBUG", "false").lower() == "true"

# CORS Configuration
CORS_ORIGINS = [
    "http://localhost:3000",  # Next.js dev server
    "http://127.0.0.1:3000",
]

# Add production frontend URL if configured
FRONTEND_URL = os.getenv("FRONTEND_URL")
if FRONTEND_URL:
    CORS_ORIGINS.append(FRONTEND_URL)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan handler.

    Startup:
    - Initialize service singletons
    - Log configuration

    Shutdown:
    - Close connections
    - Cleanup resources
    """
    # Startup
    logger.info(f"Starting analystOS API (env: {APP_ENV})")
    logger.info(f"CORS origins: {CORS_ORIGINS}")

    # Initialize services (they're lazy-loaded, but we can pre-warm them)
    from src.services.job_manager import get_job_manager_instance
    from src.services.cache_service import get_cache_service_instance
    from src.services.token_store import get_token_store_instance
    from src.services.rate_limiter import get_rate_limiter_instance

    _job_manager = get_job_manager_instance()
    _cache_service = get_cache_service_instance()
    _token_store = get_token_store_instance()
    _rate_limiter = get_rate_limiter_instance()

    logger.info("Services initialized")

    yield

    # Shutdown
    logger.info("Shutting down analystOS API")

    # Close Redis connections if in production
    if APP_ENV == "production":
        try:
            from src.services.job_manager import _job_manager as jm
            from src.services.cache_service import _cache_service as cs
            from src.services.token_store import _token_store as ts
            from src.services.rate_limiter import _rate_limiter as rl

            if hasattr(jm, "close"):
                await jm.close()
            if hasattr(cs, "close"):
                await cs.close()
            if hasattr(ts, "close"):
                await ts.close()
            if hasattr(rl, "close"):
                await rl.close()
        except Exception as e:
            logger.warning(f"Error during shutdown: {e}")

    logger.info("Shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="analystOS API",
    description="AI-powered research and analysis platform",
    version="1.0.0",
    docs_url="/docs" if DEBUG or APP_ENV == "development" else None,
    redoc_url="/redoc" if DEBUG or APP_ENV == "development" else None,
    lifespan=lifespan,
)


# ============================================================================
# Middleware (order matters - first added = outermost = runs first)
# ============================================================================

# 1. Upload size limit middleware (must be first to reject large uploads early)
app.add_middleware(LimitUploadSizeMiddleware)

# 2. CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,  # Required for cookies
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["X-Cache", "X-RateLimit-Remaining", "Retry-After"],
)


# ============================================================================
# Exception Handlers
# ============================================================================

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Global exception handler for unhandled errors."""
    logger.exception(f"Unhandled exception: {exc}")

    # Don't expose internal errors in production
    if APP_ENV == "production":
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"},
        )

    return JSONResponse(
        status_code=500,
        content={"detail": str(exc)},
    )


# ============================================================================
# Health Check
# ============================================================================

@app.get("/health")
async def health_check() -> dict:
    """
    Health check endpoint.

    Returns service status for monitoring.
    """
    return {
        "status": "healthy",
        "environment": APP_ENV,
        "version": "1.0.0",
    }


@app.get("/health/detailed")
async def detailed_health_check() -> dict:
    """
    Detailed health check with service status.

    Checks Redis connectivity in production.
    """
    services = {
        "api": "healthy",
    }

    if APP_ENV == "production":
        # Check Redis
        try:
            import redis.asyncio as aioredis
            redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
            redis_client = await aioredis.from_url(redis_url)
            await redis_client.ping()
            await redis_client.close()
            services["redis"] = "healthy"
        except Exception as e:
            services["redis"] = f"unhealthy: {e}"

    return {
        "status": "healthy" if all(v == "healthy" for v in services.values()) else "degraded",
        "environment": APP_ENV,
        "services": services,
    }


# ============================================================================
# Register Routers
# ============================================================================

# Authentication
app.include_router(auth_router)

# Research operations
app.include_router(research_router)

# Cryptocurrency
app.include_router(crypto_router)

# Notion automation
app.include_router(automation_router)

# Existing chat (preserved)
app.include_router(chat_router)


# ============================================================================
# Root Endpoint
# ============================================================================

@app.get("/")
async def root() -> dict:
    """API root - returns basic info."""
    return {
        "name": "analystOS API",
        "version": "1.0.0",
        "docs": "/docs" if DEBUG or APP_ENV == "development" else None,
    }


# ============================================================================
# Development Server
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.api_main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )

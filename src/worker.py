"""
ARQ Worker Entrypoint

Redis-backed background job worker for the research platform.
Run with: arq src.worker.WorkerSettings

Worker Configuration:
- Queue name: research
- Max concurrent jobs: 4
- Default job timeout: 30 minutes
- Result retention: 24 hours
- Max retries: 3

Job Functions:
- upload_job: Process uploaded documents
- scrape_job: Scrape URLs for content (10m timeout)
- generate_job: Generate research reports
"""

import logging
import os
from typing import Any, Dict

from arq import cron
from arq.connections import RedisSettings

from src.jobs.upload_job import upload_job
from src.jobs.scrape_job import scrape_job
from src.jobs.generate_job import generate_job

logger = logging.getLogger(__name__)

# Redis configuration
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")


def parse_redis_url(url: str) -> RedisSettings:
    """Parse Redis URL into RedisSettings."""
    from urllib.parse import urlparse

    parsed = urlparse(url)

    return RedisSettings(
        host=parsed.hostname or "localhost",
        port=parsed.port or 6379,
        password=parsed.password,
        database=int(parsed.path.lstrip("/") or 0) if parsed.path else 0,
    )


async def startup(ctx: Dict[str, Any]) -> None:
    """Worker startup hook."""
    logger.info("ARQ worker starting up")

    # Initialize any shared resources
    # These will be available in ctx during job execution

    # Example: Initialize database connection pool
    # ctx["db_pool"] = await create_db_pool()

    logger.info("ARQ worker ready")


async def shutdown(ctx: Dict[str, Any]) -> None:
    """Worker shutdown hook."""
    logger.info("ARQ worker shutting down")

    # Clean up shared resources
    # if "db_pool" in ctx:
    #     await ctx["db_pool"].close()

    logger.info("ARQ worker stopped")


async def cleanup_expired_jobs(ctx: Dict[str, Any]) -> None:
    """Cron job to clean up expired job metadata."""
    redis = ctx.get("redis")
    if not redis:
        return

    logger.info("Running expired job cleanup")

    # Scan for expired job keys
    # The job_manager sets TTL on job metadata, so Redis handles most cleanup
    # This is for any stragglers

    cursor = 0
    cleaned = 0

    while True:
        cursor, keys = await redis.scan(cursor, match="job:*", count=100)

        for key in keys:
            # Check if job is expired (no activity for 24+ hours)
            ttl = await redis.ttl(key)
            if ttl == -1:  # No TTL set
                # Set a TTL of 24 hours
                await redis.expire(key, 86400)
            elif ttl == -2:  # Key doesn't exist
                cleaned += 1

        if cursor == 0:
            break

    if cleaned > 0:
        logger.info(f"Cleaned up {cleaned} expired jobs")


# Worker settings - this is what ARQ looks for
class WorkerSettings:
    """ARQ worker settings."""

    # Job functions to register
    functions = [
        upload_job,
        scrape_job,
        generate_job,
    ]

    # Redis connection
    redis_settings = parse_redis_url(REDIS_URL)

    # Queue configuration
    queue_name = "research"
    max_jobs = 4

    # Timeouts
    job_timeout = 1800  # 30 minutes default
    max_tries = 3  # Retry failed jobs up to 3 times

    # Result retention
    keep_result = 86400  # 24 hours

    # Lifecycle hooks
    on_startup = startup
    on_shutdown = shutdown

    # Cron jobs
    cron_jobs = [
        cron(cleanup_expired_jobs, hour={0, 6, 12, 18}, minute=0),  # Every 6 hours
    ]

    # Logging
    log_results = True

    # Health check
    health_check_interval = 60  # seconds


# For running directly (development)
if __name__ == "__main__":
    import asyncio
    from arq import run_worker

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    asyncio.run(run_worker(WorkerSettings))

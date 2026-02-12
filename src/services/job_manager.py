"""
Job Manager Service

Provides a unified interface for job queue operations.
- Production: ARQ (Redis-backed) for persistence and distributed workers
- Development: asyncio.create_task for simplicity (no persistence)

Job Progress stored in Redis hash:
- job:{job_id} with fields: user_id, type, status, progress, error, timestamps
"""

import asyncio
import os
import uuid
import json
import logging
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Coroutine, Dict, Optional, TypeVar

from pydantic import BaseModel

logger = logging.getLogger(__name__)

T = TypeVar("T")


class JobStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"


class JobType(str, Enum):
    UPLOAD = "upload"
    SCRAPE = "scrape"
    GENERATE = "generate"
    EXTRACT_ENTITIES = "extract_entities"


class JobInfo(BaseModel):
    """Job metadata and status information."""
    job_id: str
    user_id: str
    job_type: JobType
    status: JobStatus
    progress: int = 0  # 0-100
    result_path: Optional[str] = None
    error: Optional[str] = None
    attempts: int = 0
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None


class JobManagerBase(ABC):
    """Abstract base class for job managers."""

    @abstractmethod
    async def create_job(
        self,
        user_id: str,
        job_type: JobType,
        func: Callable[..., Coroutine[Any, Any, T]],
        *args: Any,
        **kwargs: Any,
    ) -> str:
        """Create and enqueue a new job. Returns job_id."""
        pass

    @abstractmethod
    async def get_job(self, job_id: str) -> Optional[JobInfo]:
        """Get job status and metadata."""
        pass

    @abstractmethod
    async def update_progress(self, job_id: str, progress: int) -> None:
        """Update job progress (0-100)."""
        pass

    @abstractmethod
    async def complete_job(
        self, job_id: str, result_path: Optional[str] = None
    ) -> None:
        """Mark job as completed with optional result path."""
        pass

    @abstractmethod
    async def fail_job(self, job_id: str, error: str) -> None:
        """Mark job as failed with error message."""
        pass

    @abstractmethod
    async def cleanup_expired(self, max_age_hours: int = 24) -> int:
        """Remove expired job metadata. Returns count of removed jobs."""
        pass


class InMemoryJobManager(JobManagerBase):
    """
    Development job manager using asyncio.create_task.

    - Jobs run immediately in background tasks
    - No persistence (data lost on restart)
    - Suitable for development/testing only
    """

    def __init__(self) -> None:
        self._jobs: Dict[str, JobInfo] = {}
        self._tasks: Dict[str, asyncio.Task[Any]] = {}

    async def create_job(
        self,
        user_id: str,
        job_type: JobType,
        func: Callable[..., Coroutine[Any, Any, T]],
        *args: Any,
        **kwargs: Any,
    ) -> str:
        job_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)

        job_info = JobInfo(
            job_id=job_id,
            user_id=user_id,
            job_type=job_type,
            status=JobStatus.PENDING,
            progress=0,
            attempts=1,
            created_at=now,
            updated_at=now,
        )
        self._jobs[job_id] = job_info

        # Create wrapper that handles completion/failure
        async def job_wrapper() -> None:
            try:
                self._jobs[job_id].status = JobStatus.IN_PROGRESS
                self._jobs[job_id].updated_at = datetime.now(timezone.utc)

                # Pass job_id to function if it accepts it
                result = await func(job_id, *args, **kwargs)

                # If function returns a path, use it as result_path
                if isinstance(result, str):
                    await self.complete_job(job_id, result_path=result)
                else:
                    await self.complete_job(job_id)
            except Exception as e:
                logger.exception(f"Job {job_id} failed")
                await self.fail_job(job_id, str(e))

        task = asyncio.create_task(job_wrapper())
        self._tasks[job_id] = task
        logger.info(f"Created job {job_id} of type {job_type} for user {user_id}")
        return job_id

    async def get_job(self, job_id: str) -> Optional[JobInfo]:
        return self._jobs.get(job_id)

    async def update_progress(self, job_id: str, progress: int) -> None:
        if job_id in self._jobs:
            self._jobs[job_id].progress = min(100, max(0, progress))
            self._jobs[job_id].updated_at = datetime.now(timezone.utc)

    async def complete_job(
        self, job_id: str, result_path: Optional[str] = None
    ) -> None:
        if job_id in self._jobs:
            now = datetime.now(timezone.utc)
            self._jobs[job_id].status = JobStatus.COMPLETED
            self._jobs[job_id].progress = 100
            self._jobs[job_id].result_path = result_path
            self._jobs[job_id].updated_at = now
            self._jobs[job_id].completed_at = now
            logger.info(f"Job {job_id} completed")

    async def fail_job(self, job_id: str, error: str) -> None:
        if job_id in self._jobs:
            self._jobs[job_id].status = JobStatus.FAILED
            self._jobs[job_id].error = error
            self._jobs[job_id].updated_at = datetime.now(timezone.utc)
            logger.error(f"Job {job_id} failed: {error}")

    async def cleanup_expired(self, max_age_hours: int = 24) -> int:
        now = datetime.now(timezone.utc)
        expired = []
        for job_id, job in self._jobs.items():
            age = (now - job.created_at).total_seconds() / 3600
            if age > max_age_hours:
                expired.append(job_id)

        for job_id in expired:
            del self._jobs[job_id]
            if job_id in self._tasks:
                task = self._tasks.pop(job_id)
                if not task.done():
                    task.cancel()

        return len(expired)


class RedisJobManager(JobManagerBase):
    """
    Production job manager using ARQ (Redis-backed).

    - Jobs are persisted in Redis
    - Supports distributed workers
    - Automatic retries with exponential backoff
    """

    def __init__(self, redis_url: str = "redis://localhost:6379") -> None:
        self._redis_url = redis_url
        self._redis: Any = None
        self._arq_pool: Any = None

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

    async def _get_arq_pool(self) -> Any:
        """Lazy ARQ pool initialization."""
        if self._arq_pool is None:
            try:
                from arq import create_pool
                from arq.connections import RedisSettings

                # Parse Redis URL
                settings = RedisSettings.from_dsn(self._redis_url)
                self._arq_pool = await create_pool(settings)
            except ImportError:
                raise RuntimeError("arq package required for production mode")
        return self._arq_pool

    def _job_key(self, job_id: str) -> str:
        return f"job:{job_id}"

    async def create_job(
        self,
        user_id: str,
        job_type: JobType,
        func: Callable[..., Coroutine[Any, Any, T]],
        *args: Any,
        **kwargs: Any,
    ) -> str:
        job_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)

        job_info = JobInfo(
            job_id=job_id,
            user_id=user_id,
            job_type=job_type,
            status=JobStatus.PENDING,
            progress=0,
            attempts=1,
            created_at=now,
            updated_at=now,
        )

        redis = await self._get_redis()

        # Store job metadata in Redis hash
        job_data = job_info.model_dump(mode="json")
        job_data["created_at"] = job_info.created_at.isoformat()
        job_data["updated_at"] = job_info.updated_at.isoformat()

        await redis.hset(self._job_key(job_id), mapping={
            k: json.dumps(v) if isinstance(v, (dict, list)) else str(v) if v is not None else ""
            for k, v in job_data.items()
        })
        # Set TTL of 24 hours on job metadata
        await redis.expire(self._job_key(job_id), 86400)

        # Enqueue job via ARQ
        pool = await self._get_arq_pool()

        # Job function name must match registered ARQ functions
        arq_func_name = f"{job_type.value}_job"

        # Determine timeout based on job type
        timeout = 600 if job_type == JobType.SCRAPE else 1800

        await pool.enqueue_job(
            arq_func_name,
            job_id,
            *args,
            _job_timeout=timeout,
            **kwargs,
        )

        logger.info(f"Created ARQ job {job_id} of type {job_type} for user {user_id}")
        return job_id

    async def get_job(self, job_id: str) -> Optional[JobInfo]:
        redis = await self._get_redis()
        data = await redis.hgetall(self._job_key(job_id))

        if not data:
            return None

        # Parse the stored data
        return JobInfo(
            job_id=data.get("job_id", job_id),
            user_id=data.get("user_id", ""),
            job_type=JobType(data.get("job_type", "upload")),
            status=JobStatus(data.get("status", "pending")),
            progress=int(data.get("progress", 0)),
            result_path=data.get("result_path") or None,
            error=data.get("error") or None,
            attempts=int(data.get("attempts", 0)),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else datetime.now(timezone.utc),
            updated_at=datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else datetime.now(timezone.utc),
            completed_at=datetime.fromisoformat(data["completed_at"]) if data.get("completed_at") else None,
        )

    async def update_progress(self, job_id: str, progress: int) -> None:
        redis = await self._get_redis()
        await redis.hset(
            self._job_key(job_id),
            mapping={
                "progress": str(min(100, max(0, progress))),
                "updated_at": datetime.now(timezone.utc).isoformat(),
            },
        )

    async def complete_job(
        self, job_id: str, result_path: Optional[str] = None
    ) -> None:
        redis = await self._get_redis()
        now = datetime.now(timezone.utc)
        mapping = {
            "status": JobStatus.COMPLETED.value,
            "progress": "100",
            "updated_at": now.isoformat(),
            "completed_at": now.isoformat(),
        }
        if result_path:
            mapping["result_path"] = result_path
        await redis.hset(self._job_key(job_id), mapping=mapping)
        logger.info(f"Job {job_id} completed")

    async def fail_job(self, job_id: str, error: str) -> None:
        redis = await self._get_redis()
        await redis.hset(
            self._job_key(job_id),
            mapping={
                "status": JobStatus.FAILED.value,
                "error": error,
                "updated_at": datetime.now(timezone.utc).isoformat(),
            },
        )
        logger.error(f"Job {job_id} failed: {error}")

    async def cleanup_expired(self, max_age_hours: int = 24) -> int:
        # Redis TTL handles expiration automatically
        # This method is for manual cleanup if needed
        return 0

    async def close(self) -> None:
        """Close Redis connections."""
        if self._redis:
            await self._redis.close()
        if self._arq_pool:
            await self._arq_pool.close()


def get_job_manager() -> JobManagerBase:
    """
    Factory function to get the appropriate job manager.

    Returns InMemoryJobManager for development, RedisJobManager for production.
    """
    app_env = os.getenv("APP_ENV", "development")

    if app_env == "production":
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        return RedisJobManager(redis_url)

    return InMemoryJobManager()


# Module-level singleton
_job_manager: Optional[JobManagerBase] = None


def get_job_manager_instance() -> JobManagerBase:
    """Get or create the singleton job manager instance."""
    global _job_manager
    if _job_manager is None:
        _job_manager = get_job_manager()
    return _job_manager

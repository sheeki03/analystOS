# Services package

"""
Core services for the analystOS platform.

Services:
- job_manager: Async job queue (ARQ prod, asyncio dev)
- cache_service: TTL cache with stale-while-error
- token_store: Refresh token storage with family tracking
- rate_limiter: Sliding window rate limiter
- upload_middleware: Upload size enforcement
"""

from src.services.job_manager import (
    get_job_manager_instance,
    JobManagerBase,
    JobInfo,
    JobStatus,
    JobType,
)
from src.services.cache_service import (
    get_cache_service_instance,
    CacheServiceBase,
    CacheStatus,
    CacheConfig,
)
from src.services.token_store import (
    get_token_store_instance,
    TokenStoreBase,
    generate_token,
    generate_family_id,
    hash_token,
)
from src.services.rate_limiter import (
    get_rate_limiter_instance,
    RateLimiterBase,
    RateLimitResult,
    get_client_ip,
    get_rate_limit_key,
    get_rate_limit_config,
)
from src.services.upload_middleware import (
    LimitUploadSizeMiddleware,
    validate_file_extension,
    validate_mime_type,
    validate_upload_file,
    validate_url_batch,
    validate_sitemap_urls,
    ALLOWED_EXTENSIONS,
)

__all__ = [
    # Job Manager
    "get_job_manager_instance",
    "JobManagerBase",
    "JobInfo",
    "JobStatus",
    "JobType",
    # Cache Service
    "get_cache_service_instance",
    "CacheServiceBase",
    "CacheStatus",
    "CacheConfig",
    # Token Store
    "get_token_store_instance",
    "TokenStoreBase",
    "generate_token",
    "generate_family_id",
    "hash_token",
    # Rate Limiter
    "get_rate_limiter_instance",
    "RateLimiterBase",
    "RateLimitResult",
    "get_client_ip",
    "get_rate_limit_key",
    "get_rate_limit_config",
    # Upload Middleware
    "LimitUploadSizeMiddleware",
    "validate_file_extension",
    "validate_mime_type",
    "validate_upload_file",
    "validate_url_batch",
    "validate_sitemap_urls",
    "ALLOWED_EXTENSIONS",
]
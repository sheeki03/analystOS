"""
Job Models

Pydantic models for async job operations:
- Job creation responses
- Job status queries
- Job progress updates
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class JobStatus(str, Enum):
    """Job execution status."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"


class JobType(str, Enum):
    """Types of background jobs."""
    UPLOAD = "upload"
    SCRAPE = "scrape"
    GENERATE = "generate"
    EXTRACT_ENTITIES = "extract_entities"


class JobCreatedResponse(BaseModel):
    """Response when a job is created."""
    job_id: str
    job_type: JobType
    status: JobStatus = JobStatus.PENDING
    message: str = "Job created successfully"


class JobStatusResponse(BaseModel):
    """Response for job status query."""
    job_id: str
    user_id: str
    job_type: JobType
    status: JobStatus
    progress: int = Field(..., ge=0, le=100)
    result_path: Optional[str] = None
    error: Optional[str] = None
    attempts: int = 0
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None


class JobProgressUpdate(BaseModel):
    """Progress update for a running job."""
    job_id: str
    progress: int = Field(..., ge=0, le=100)
    message: Optional[str] = None


class JobListItem(BaseModel):
    """Compact job info for list views."""
    job_id: str
    job_type: JobType
    status: JobStatus
    progress: int = Field(..., ge=0, le=100)
    created_at: datetime


class JobListResponse(BaseModel):
    """Response for listing jobs."""
    jobs: List[JobListItem]
    total: int
    page: int = 1
    page_size: int = 20

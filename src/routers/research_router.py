"""
Research Router

Async job-based research endpoints:
- POST /research/upload - Upload documents for processing
- POST /research/scrape - Scrape URLs for content
- POST /research/generate - Generate research report
- POST /research/extract-entities - Extract entities from sources
- GET /research/jobs/{job_id} - Get job status
- GET /research/reports - List user's reports
- GET /research/reports/{id} - Get full report
- GET /research/reports/{id}/download - Download report file

All operations that take time return a job_id immediately.
Poll /jobs/{job_id} to check status.
"""

import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    UploadFile,
    status,
)
from fastapi.responses import FileResponse, StreamingResponse

from src.models.auth_models import TokenPayload
from src.models.job_models import JobCreatedResponse, JobStatusResponse, JobType
from src.models.research_models import (
    EntityExtractionRequest,
    EntityExtractionResponse,
    GenerateRequest,
    GenerateResponse,
    ReportDetail,
    ReportListResponse,
    ReportSummary,
    ScrapeRequest,
    ScrapeResponse,
    UploadResponse,
)
from src.routers.auth_router import get_current_user
from src.services.job_manager import (
    JobInfo,
    JobStatus,
    JobType as JMJobType,
    get_job_manager_instance,
    JobManagerBase,
)
from src.services.upload_middleware import (
    validate_file_extension,
    validate_mime_type,
    validate_url_batch,
    validate_sitemap_urls,
    ALLOWED_EXTENSIONS,
)

logger = logging.getLogger(__name__)

# Configuration
REPORTS_DIR = Path(os.getenv("REPORTS_DIR", "reports"))
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

router = APIRouter(prefix="/research", tags=["Research"])


# ============================================================================
# Dependencies
# ============================================================================

def get_job_manager() -> JobManagerBase:
    """Dependency to get job manager instance."""
    return get_job_manager_instance()


# ============================================================================
# Job Functions (placeholders - real implementations in jobs/*.py)
# ============================================================================

async def _upload_job(
    job_id: str,
    user_id: str,
    filenames: List[str],
    file_contents: List[bytes],
) -> str:
    """Process uploaded documents. Returns result path."""
    job_manager = get_job_manager_instance()

    try:
        await job_manager.update_progress(job_id, 10)

        # TODO: Integrate with actual document processing
        # For now, save files and mark complete
        user_dir = REPORTS_DIR / user_id
        user_dir.mkdir(parents=True, exist_ok=True)

        for i, (filename, content) in enumerate(zip(filenames, file_contents)):
            file_path = user_dir / f"{job_id}_{filename}"
            file_path.write_bytes(content)
            progress = 10 + int(80 * (i + 1) / len(filenames))
            await job_manager.update_progress(job_id, progress)

        await job_manager.update_progress(job_id, 100)
        logger.info(f"Upload job {job_id} completed: {len(filenames)} files")

        return str(user_dir / job_id)

    except Exception as e:
        logger.exception(f"Upload job {job_id} failed")
        raise


async def _scrape_job(
    job_id: str,
    user_id: str,
    urls: List[str],
) -> str:
    """Scrape URLs for content. Returns result path."""
    job_manager = get_job_manager_instance()

    try:
        await job_manager.update_progress(job_id, 10)

        # TODO: Integrate with FireCrawl or existing scraper
        # For now, placeholder implementation
        user_dir = REPORTS_DIR / user_id
        user_dir.mkdir(parents=True, exist_ok=True)

        for i, url in enumerate(urls):
            # Placeholder: would actually scrape here
            progress = 10 + int(80 * (i + 1) / len(urls))
            await job_manager.update_progress(job_id, progress)

        await job_manager.update_progress(job_id, 100)
        logger.info(f"Scrape job {job_id} completed: {len(urls)} URLs")

        return str(user_dir / job_id)

    except Exception as e:
        logger.exception(f"Scrape job {job_id} failed")
        raise


async def _generate_job(
    job_id: str,
    user_id: str,
    model: str,
    sources: List[str],
    query: Optional[str],
) -> str:
    """Generate research report. Returns result path."""
    job_manager = get_job_manager_instance()

    try:
        await job_manager.update_progress(job_id, 10)

        # TODO: Integrate with research_engine.py
        # For now, placeholder implementation
        user_dir = REPORTS_DIR / user_id
        user_dir.mkdir(parents=True, exist_ok=True)

        report_path = user_dir / f"{job_id}.md"

        # Placeholder report
        report_content = f"""# Research Report

Generated: {datetime.now(timezone.utc).isoformat()}
Model: {model}
Sources: {len(sources)}

## Query
{query or "General analysis"}

## Content

This is a placeholder report. Real implementation will use the research engine.
"""

        await job_manager.update_progress(job_id, 50)

        report_path.write_text(report_content)

        await job_manager.update_progress(job_id, 100)
        logger.info(f"Generate job {job_id} completed")

        return str(report_path)

    except Exception as e:
        logger.exception(f"Generate job {job_id} failed")
        raise


async def _extract_entities_job(
    job_id: str,
    user_id: str,
    sources: List[str],
) -> str:
    """Extract entities from sources. Returns result path."""
    job_manager = get_job_manager_instance()

    try:
        await job_manager.update_progress(job_id, 10)

        # TODO: Integrate with langextract_service.py
        # For now, placeholder implementation
        user_dir = REPORTS_DIR / user_id
        user_dir.mkdir(parents=True, exist_ok=True)

        await job_manager.update_progress(job_id, 100)
        logger.info(f"Entity extraction job {job_id} completed")

        return str(user_dir / job_id)

    except Exception as e:
        logger.exception(f"Entity extraction job {job_id} failed")
        raise


# ============================================================================
# Upload Endpoints
# ============================================================================

@router.post("/upload", response_model=UploadResponse)
async def upload_documents(
    files: List[UploadFile] = File(...),
    current_user: TokenPayload = Depends(get_current_user),
    job_manager: JobManagerBase = Depends(get_job_manager),
) -> UploadResponse:
    """
    Upload documents for processing.

    Accepts: .pdf, .docx, .txt, .md files
    Max size: 50MB total (enforced by middleware)
    Max files: 10 per request

    Returns job_id to poll for status.
    """
    if len(files) > 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum 10 files per upload",
        )

    # Validate files
    filenames = []
    file_contents = []

    for file in files:
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File must have a filename",
            )

        if not validate_file_extension(file.filename):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid file extension. Allowed: {ALLOWED_EXTENSIONS}",
            )

        # Read file content
        content = await file.read()

        # Validate MIME type
        if not validate_mime_type(content, file.filename):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File content does not match expected type: {file.filename}",
            )

        filenames.append(file.filename)
        file_contents.append(content)

    # Create job
    job_id = await job_manager.create_job(
        user_id=current_user.sub,
        job_type=JMJobType.UPLOAD,
        func=_upload_job,
        filenames=filenames,
        file_contents=file_contents,
    )

    return UploadResponse(
        job_id=job_id,
        filenames=filenames,
        message=f"Upload started for {len(filenames)} files",
    )


# ============================================================================
# Scrape Endpoints
# ============================================================================

@router.post("/scrape", response_model=ScrapeResponse)
async def scrape_urls(
    request: ScrapeRequest,
    current_user: TokenPayload = Depends(get_current_user),
    job_manager: JobManagerBase = Depends(get_job_manager),
) -> ScrapeResponse:
    """
    Scrape URLs or sitemap for content.

    - urls: List of up to 10 URLs to scrape
    - sitemap_url: URL of sitemap.xml (max 100 URLs extracted)

    Provide either urls OR sitemap_url, not both.
    Returns job_id to poll for status.
    """
    urls_to_scrape: List[str] = []

    if request.urls and request.sitemap_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provide either urls or sitemap_url, not both",
        )

    if request.urls:
        # Validate URL batch
        is_valid, error = validate_url_batch(request.urls)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error,
            )
        urls_to_scrape = request.urls

    elif request.sitemap_url:
        # TODO: Parse sitemap and extract URLs
        # For now, just use the sitemap URL as a single URL
        import validators
        if not validators.url(request.sitemap_url):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid sitemap URL: {request.sitemap_url}",
            )
        # Placeholder: would parse sitemap here
        urls_to_scrape = [request.sitemap_url]

    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provide urls or sitemap_url",
        )

    # Create job
    job_id = await job_manager.create_job(
        user_id=current_user.sub,
        job_type=JMJobType.SCRAPE,
        func=_scrape_job,
        urls=urls_to_scrape,
    )

    return ScrapeResponse(
        job_id=job_id,
        url_count=len(urls_to_scrape),
        message=f"Scraping started for {len(urls_to_scrape)} URLs",
    )


# ============================================================================
# Generate Endpoints
# ============================================================================

@router.post("/generate", response_model=GenerateResponse)
async def generate_report(
    request: GenerateRequest,
    current_user: TokenPayload = Depends(get_current_user),
    job_manager: JobManagerBase = Depends(get_job_manager),
) -> GenerateResponse:
    """
    Generate a research report from sources.

    - model: AI model to use (e.g., "anthropic/claude-sonnet-4.5")
    - sources: List of source job IDs (from upload/scrape)
    - query: Optional specific research focus

    Returns job_id to poll for status.
    """
    if not request.sources:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one source is required",
        )

    # TODO: Validate that sources exist and belong to user

    # Create job
    job_id = await job_manager.create_job(
        user_id=current_user.sub,
        job_type=JMJobType.GENERATE,
        func=_generate_job,
        model=request.model,
        sources=request.sources,
        query=request.query,
    )

    return GenerateResponse(
        job_id=job_id,
        model=request.model,
        source_count=len(request.sources),
        message="Report generation started",
    )


# ============================================================================
# Entity Extraction Endpoints
# ============================================================================

@router.post("/extract-entities", response_model=EntityExtractionResponse)
async def extract_entities(
    request: EntityExtractionRequest,
    current_user: TokenPayload = Depends(get_current_user),
    job_manager: JobManagerBase = Depends(get_job_manager),
) -> EntityExtractionResponse:
    """
    Extract entities (people, orgs, tech) from sources.

    - sources: List of source job IDs

    Returns job_id to poll for status.
    """
    if not request.sources:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one source is required",
        )

    # Create job
    job_id = await job_manager.create_job(
        user_id=current_user.sub,
        job_type=JMJobType.EXTRACT_ENTITIES,
        func=_extract_entities_job,
        sources=request.sources,
    )

    return EntityExtractionResponse(
        job_id=job_id,
        message="Entity extraction started",
    )


# ============================================================================
# Job Status Endpoints
# ============================================================================

@router.get("/jobs/{job_id}", response_model=JobStatusResponse)
async def get_job_status(
    job_id: str,
    current_user: TokenPayload = Depends(get_current_user),
    job_manager: JobManagerBase = Depends(get_job_manager),
) -> JobStatusResponse:
    """
    Get status of a job.

    Returns current status, progress, and result/error if complete.
    """
    job_info = await job_manager.get_job(job_id)

    if job_info is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found",
        )

    # Verify ownership
    if job_info.user_id != current_user.sub:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this job",
        )

    return JobStatusResponse(
        job_id=job_info.job_id,
        user_id=job_info.user_id,
        job_type=JobType(job_info.job_type.value),
        status=job_info.status,
        progress=job_info.progress,
        result_path=job_info.result_path,
        error=job_info.error,
        attempts=job_info.attempts,
        created_at=job_info.created_at,
        updated_at=job_info.updated_at,
        completed_at=job_info.completed_at,
    )


# ============================================================================
# Report Endpoints
# ============================================================================

@router.get("/reports", response_model=ReportListResponse)
async def list_reports(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: TokenPayload = Depends(get_current_user),
) -> ReportListResponse:
    """
    List user's completed reports.

    Paginated list of report summaries.
    """
    # TODO: Query from database/storage
    # For now, scan reports directory
    user_dir = REPORTS_DIR / current_user.sub

    reports: List[ReportSummary] = []

    if user_dir.exists():
        for report_file in user_dir.glob("*.md"):
            stat = report_file.stat()
            content = report_file.read_text()

            reports.append(ReportSummary(
                report_id=report_file.stem,
                title=f"Report {report_file.stem[:8]}",
                model="unknown",
                source_count=0,
                created_at=datetime.fromtimestamp(stat.st_ctime, tz=timezone.utc),
                word_count=len(content.split()),
            ))

    # Sort by created_at descending
    reports.sort(key=lambda r: r.created_at, reverse=True)

    # Paginate
    total = len(reports)
    start = (page - 1) * page_size
    end = start + page_size
    reports = reports[start:end]

    return ReportListResponse(
        reports=reports,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/reports/{report_id}", response_model=ReportDetail)
async def get_report(
    report_id: str,
    current_user: TokenPayload = Depends(get_current_user),
) -> ReportDetail:
    """
    Get full report content.

    Returns complete report with content and metadata.
    """
    user_dir = REPORTS_DIR / current_user.sub
    report_path = user_dir / f"{report_id}.md"

    if not report_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found",
        )

    content = report_path.read_text()
    stat = report_path.stat()

    return ReportDetail(
        report_id=report_id,
        title=f"Report {report_id[:8]}",
        model="unknown",
        content=content,
        sources=[],
        created_at=datetime.fromtimestamp(stat.st_ctime, tz=timezone.utc),
        word_count=len(content.split()),
    )


@router.get("/reports/{report_id}/download")
async def download_report(
    report_id: str,
    current_user: TokenPayload = Depends(get_current_user),
) -> FileResponse:
    """
    Download report as file.

    Streams the report file with proper content headers.
    Logs access for audit trail.
    """
    user_dir = REPORTS_DIR / current_user.sub
    report_path = user_dir / f"{report_id}.md"

    if not report_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found",
        )

    # Log download for audit
    logger.info(f"User {current_user.username} downloaded report {report_id}")

    return FileResponse(
        path=report_path,
        filename=f"report-{report_id[:8]}.md",
        media_type="text/markdown",
    )

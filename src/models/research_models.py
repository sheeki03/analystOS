"""
Research Models

Pydantic models for research endpoints:
- Document upload
- URL scraping
- Report generation
- Entity extraction
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, HttpUrl


class SourceType(str, Enum):
    """Source type for research content."""
    DOCUMENT = "document"
    URL = "url"
    SITEMAP = "sitemap"


class UploadMode(str, Enum):
    """Upload/input mode."""
    SINGLE = "single"
    BULK = "bulk"
    SITEMAP = "sitemap"


# Upload Models

class UploadResponse(BaseModel):
    """Response after initiating document upload."""
    job_id: str
    filenames: List[str]
    message: str = "Upload started"


class UploadProgress(BaseModel):
    """Progress update during upload processing."""
    job_id: str
    files_processed: int
    total_files: int
    current_file: Optional[str] = None


# Scrape Models

class ScrapeRequest(BaseModel):
    """Request to scrape URLs."""
    urls: Optional[List[str]] = Field(None, max_length=10)
    sitemap_url: Optional[str] = None

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "urls": ["https://example.com/page1", "https://example.com/page2"]
                },
                {
                    "sitemap_url": "https://example.com/sitemap.xml"
                }
            ]
        }


class ScrapeResponse(BaseModel):
    """Response after initiating URL scraping."""
    job_id: str
    url_count: int
    message: str = "Scraping started"


# Generate Models

class GenerateRequest(BaseModel):
    """Request to generate a research report."""
    model: str = Field(..., description="AI model to use for generation")
    sources: List[str] = Field(..., description="List of source IDs (document/URL job IDs)")
    query: Optional[str] = Field(None, description="Specific research query/focus")

    class Config:
        json_schema_extra = {
            "example": {
                "model": "anthropic/claude-sonnet-4.5",
                "sources": ["job-uuid-1", "job-uuid-2"],
                "query": "Analyze the tokenomics and governance structure"
            }
        }


class GenerateResponse(BaseModel):
    """Response after initiating report generation."""
    job_id: str
    model: str
    source_count: int
    message: str = "Report generation started"


# Entity Extraction Models

class EntityExtractionRequest(BaseModel):
    """Request to extract entities from sources."""
    sources: List[str] = Field(..., description="List of source IDs")


class EntityExtractionResponse(BaseModel):
    """Response after initiating entity extraction."""
    job_id: str
    message: str = "Entity extraction started"


class ExtractedEntity(BaseModel):
    """A single extracted entity."""
    entity_type: str  # person, organization, technology, etc.
    name: str
    description: Optional[str] = None
    confidence: float = Field(..., ge=0, le=1)
    source_refs: List[str] = []  # References to source documents


class EntityExtractionResult(BaseModel):
    """Result of entity extraction."""
    people: List[ExtractedEntity] = []
    organizations: List[ExtractedEntity] = []
    technologies: List[ExtractedEntity] = []
    locations: List[ExtractedEntity] = []
    other: List[ExtractedEntity] = []


# Report Models

class ReportSummary(BaseModel):
    """Summary of a research report for list views."""
    report_id: str
    title: str
    model: str
    source_count: int
    created_at: datetime
    word_count: Optional[int] = None


class ReportListResponse(BaseModel):
    """Response for listing user's reports."""
    reports: List[ReportSummary]
    total: int
    page: int = 1
    page_size: int = 20


class ReportDetail(BaseModel):
    """Full report details."""
    report_id: str
    title: str
    model: str
    content: str  # Markdown content
    sources: List[str]
    entities: Optional[EntityExtractionResult] = None
    created_at: datetime
    word_count: int


class ReportDownloadInfo(BaseModel):
    """Information for report download."""
    report_id: str
    filename: str
    content_type: str
    size_bytes: int


# Crypto Chat Models (for research context)

class CryptoResearchContext(BaseModel):
    """Context for crypto-aware research."""
    coin_ids: List[str] = []
    topics: List[str] = []
    time_range: Optional[str] = None  # e.g., "7d", "30d", "1y"

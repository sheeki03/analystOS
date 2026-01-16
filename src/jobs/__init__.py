"""
ARQ Job Functions

Background job functions for the research platform.
These are registered with the ARQ worker for Redis-backed job processing.

Job functions:
- upload_job: Process uploaded documents
- scrape_job: Scrape URLs for content
- generate_job: Generate research reports
- extract_entities_job: Extract entities from sources
"""

from src.jobs.upload_job import upload_job
from src.jobs.scrape_job import scrape_job
from src.jobs.generate_job import generate_job

__all__ = [
    "upload_job",
    "scrape_job",
    "generate_job",
]

"""
Scrape Job

ARQ job function for scraping URLs.
Uses FireCrawl or Playwright for content extraction.

Flow:
1. Validate URLs
2. Scrape each URL
3. Extract and clean content
4. Store results
5. Update job progress
"""

import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

# Configuration
REPORTS_DIR = Path(os.getenv("REPORTS_DIR", "reports"))
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

# Scrape timeout per URL (seconds)
SCRAPE_TIMEOUT = 30


async def scrape_job(
    ctx: Dict[str, Any],
    job_id: str,
    user_id: str,
    urls: List[str],
) -> Dict[str, Any]:
    """
    Scrape URLs for content.

    Args:
        ctx: ARQ context (contains redis connection)
        job_id: Unique job identifier
        user_id: Owner user ID
        urls: List of URLs to scrape

    Returns:
        Dict with result_path and scraped content info
    """
    redis = ctx.get("redis")

    try:
        logger.info(f"Starting scrape job {job_id} for {len(urls)} URLs")

        # Update progress
        if redis:
            await redis.hset(f"job:{job_id}", mapping={
                "status": "in_progress",
                "progress": "10",
            })

        # Create user directory
        user_dir = REPORTS_DIR / user_id
        user_dir.mkdir(parents=True, exist_ok=True)

        # Scrape each URL
        scraped_content = []

        for i, url in enumerate(urls):
            logger.debug(f"Scraping URL {i+1}/{len(urls)}: {url}")

            try:
                content = await _scrape_url(url)

                scraped_content.append({
                    "url": url,
                    "success": True,
                    "char_count": len(content),
                    "word_count": len(content.split()),
                })

                # Save content
                safe_filename = _url_to_filename(url)
                output_path = user_dir / f"{job_id}_{safe_filename}.txt"
                output_path.write_text(content)

            except Exception as e:
                logger.warning(f"Failed to scrape {url}: {e}")
                scraped_content.append({
                    "url": url,
                    "success": False,
                    "error": str(e),
                })

            # Update progress
            progress = 10 + int(80 * (i + 1) / len(urls))
            if redis:
                await redis.hset(f"job:{job_id}", "progress", str(progress))

        # Finalize
        result_path = str(user_dir / job_id)

        # Count successes
        success_count = sum(1 for s in scraped_content if s.get("success"))

        if redis:
            await redis.hset(f"job:{job_id}", mapping={
                "status": "completed",
                "progress": "100",
                "result_path": result_path,
                "completed_at": datetime.now(timezone.utc).isoformat(),
            })

        logger.info(f"Scrape job {job_id} completed: {success_count}/{len(urls)} URLs")

        return {
            "result_path": result_path,
            "urls": scraped_content,
            "success_count": success_count,
            "total_count": len(urls),
        }

    except Exception as e:
        logger.exception(f"Scrape job {job_id} failed")

        if redis:
            await redis.hset(f"job:{job_id}", mapping={
                "status": "failed",
                "error": str(e),
            })

        raise


async def _scrape_url(url: str) -> str:
    """
    Scrape content from a URL.

    Tries FireCrawl first, falls back to httpx + BeautifulSoup.
    """
    # Try FireCrawl if available
    try:
        return await _scrape_with_firecrawl(url)
    except Exception as e:
        logger.debug(f"FireCrawl failed, trying fallback: {e}")

    # Fallback to httpx + BeautifulSoup
    return await _scrape_with_httpx(url)


async def _scrape_with_firecrawl(url: str) -> str:
    """Scrape using FireCrawl API."""
    import os

    api_key = os.getenv("FIRECRAWL_API_KEY")
    if not api_key:
        raise RuntimeError("FIRECRAWL_API_KEY not set")

    from firecrawl import FirecrawlApp

    app = FirecrawlApp(api_key=api_key)
    result = app.scrape_url(url, params={"formats": ["markdown"]})

    if result and "markdown" in result:
        return result["markdown"]

    raise RuntimeError("FireCrawl returned no content")


async def _scrape_with_httpx(url: str) -> str:
    """Scrape using httpx and BeautifulSoup."""
    import httpx
    from bs4 import BeautifulSoup

    async with httpx.AsyncClient(timeout=SCRAPE_TIMEOUT) as client:
        response = await client.get(url, follow_redirects=True)
        response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    # Remove script and style elements
    for script in soup(["script", "style", "nav", "footer", "header"]):
        script.decompose()

    # Get text
    text = soup.get_text(separator="\n", strip=True)

    # Clean up whitespace
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return "\n\n".join(lines)


def _url_to_filename(url: str) -> str:
    """Convert URL to safe filename."""
    import re
    from urllib.parse import urlparse

    parsed = urlparse(url)
    # Use domain and path
    name = f"{parsed.netloc}{parsed.path}"
    # Remove unsafe characters
    name = re.sub(r"[^a-zA-Z0-9_-]", "_", name)
    # Limit length
    return name[:50]

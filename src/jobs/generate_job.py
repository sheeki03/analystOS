"""
Generate Job

ARQ job function for generating research reports.
Uses the research engine to create comprehensive reports.

Flow:
1. Load source content from previous jobs
2. Build context for AI
3. Generate report using selected model
4. Store result
5. Update job progress
"""

import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Configuration
REPORTS_DIR = Path(os.getenv("REPORTS_DIR", "reports"))
REPORTS_DIR.mkdir(parents=True, exist_ok=True)


async def generate_job(
    ctx: Dict[str, Any],
    job_id: str,
    user_id: str,
    model: str,
    sources: List[str],
    query: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Generate a research report from sources.

    Args:
        ctx: ARQ context (contains redis connection)
        job_id: Unique job identifier
        user_id: Owner user ID
        model: AI model to use for generation
        sources: List of source job IDs
        query: Optional specific research focus

    Returns:
        Dict with result_path and report metadata
    """
    redis = ctx.get("redis")

    try:
        logger.info(f"Starting generate job {job_id} with model {model}")

        # Update progress
        if redis:
            await redis.hset(f"job:{job_id}", mapping={
                "status": "in_progress",
                "progress": "10",
            })

        # Create user directory
        user_dir = REPORTS_DIR / user_id
        user_dir.mkdir(parents=True, exist_ok=True)

        # Load source content
        source_content = await _load_sources(user_id, sources)

        if redis:
            await redis.hset(f"job:{job_id}", "progress", "30")

        # Generate report
        report_content = await _generate_report(
            model=model,
            sources=source_content,
            query=query,
        )

        if redis:
            await redis.hset(f"job:{job_id}", "progress", "90")

        # Save report
        report_path = user_dir / f"{job_id}.md"
        report_path.write_text(report_content)

        # Calculate metadata
        word_count = len(report_content.split())

        # Finalize
        if redis:
            await redis.hset(f"job:{job_id}", mapping={
                "status": "completed",
                "progress": "100",
                "result_path": str(report_path),
                "completed_at": datetime.now(timezone.utc).isoformat(),
            })

        logger.info(f"Generate job {job_id} completed: {word_count} words")

        return {
            "result_path": str(report_path),
            "word_count": word_count,
            "model": model,
            "source_count": len(sources),
        }

    except Exception as e:
        logger.exception(f"Generate job {job_id} failed")

        if redis:
            await redis.hset(f"job:{job_id}", mapping={
                "status": "failed",
                "error": str(e),
            })

        raise


async def _load_sources(user_id: str, source_ids: List[str]) -> List[Dict[str, str]]:
    """Load content from source jobs."""
    user_dir = REPORTS_DIR / user_id
    sources = []

    for source_id in source_ids:
        # Look for files matching this source ID
        for file_path in user_dir.glob(f"{source_id}*.txt"):
            content = file_path.read_text()
            sources.append({
                "source_id": source_id,
                "filename": file_path.name,
                "content": content,
            })

    logger.debug(f"Loaded {len(sources)} source files for generation")
    if not sources:
        raise FileNotFoundError(f"No sources found for user '{user_id}' in {user_dir}")
    return sources


async def _generate_report(
    model: str,
    sources: List[Dict[str, str]],
    query: Optional[str] = None,
) -> str:
    """Generate research report using AI model."""
    # TODO: Integrate with existing research_engine.py
    # This is a placeholder implementation

    # Build context from sources
    context_parts = []
    for source in sources:
        context_parts.append(f"### Source: {source['filename']}\n\n{source['content']}")

    context = "\n\n---\n\n".join(context_parts)

    # Build prompt
    query_text = query or "Provide a comprehensive analysis of the provided materials."

    prompt = f"""Based on the following source materials, please generate a comprehensive research report.

## Research Query
{query_text}

## Source Materials
{context}

## Instructions
Please provide a detailed, well-structured research report following this format:

1. Executive Summary
2. Key Findings
3. Detailed Analysis
4. Risk Assessment
5. Recommendations
6. Appendices & Sources

Ensure the report is thorough, evidence-based, and professionally written.
"""

    # Try to use OpenRouter for generation
    try:
        report = await _call_openrouter(model, prompt)
        return report
    except Exception as e:
        logger.warning(f"OpenRouter call failed: {e}")

    # Fallback to placeholder
    return _generate_placeholder_report(query, sources)


async def _call_openrouter(model: str, prompt: str) -> str:
    """Call OpenRouter API for report generation."""
    import httpx
    import os

    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise RuntimeError("OPENROUTER_API_KEY not set")

    base_url = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")

    async with httpx.AsyncClient(timeout=300) as client:
        response = await client.post(
            f"{base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": model,
                "messages": [
                    {"role": "user", "content": prompt},
                ],
                "max_tokens": 8000,
            },
        )
        response.raise_for_status()

    result = response.json()
    return result["choices"][0]["message"]["content"]


def _generate_placeholder_report(query: Optional[str], sources: List[Dict[str, str]]) -> str:
    """Generate a placeholder report when AI is unavailable."""
    now = datetime.now(timezone.utc)

    source_list = "\n".join(f"- {s['filename']}" for s in sources)

    return f"""# Research Report

**Generated:** {now.isoformat()}
**Model:** Placeholder (AI unavailable)
**Sources:** {len(sources)} documents

## Query
{query or "General analysis"}

## Sources Analyzed
{source_list}

## Note
This is a placeholder report. The AI model was unavailable for report generation.
Please check your OPENROUTER_API_KEY configuration and retry.

## Source Content Preview
The following sources were provided for analysis:

{"\n\n---\n\n".join(s['content'][:500] + '...' for s in sources[:3])}
"""

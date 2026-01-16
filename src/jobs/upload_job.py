"""
Upload Job

ARQ job function for processing uploaded documents.
Handles PDF, DOCX, TXT, and MD files.

Flow:
1. Validate files
2. Extract text content
3. Store processed content
4. Update job progress
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


async def upload_job(
    ctx: Dict[str, Any],
    job_id: str,
    user_id: str,
    filenames: List[str],
    file_contents: List[bytes],
) -> Dict[str, Any]:
    """
    Process uploaded documents.

    Args:
        ctx: ARQ context (contains redis connection)
        job_id: Unique job identifier
        user_id: Owner user ID
        filenames: List of uploaded filenames
        file_contents: List of file contents as bytes

    Returns:
        Dict with result_path and processed file info
    """
    redis = ctx.get("redis")

    try:
        logger.info(f"Starting upload job {job_id} for {len(filenames)} files")

        # Update progress
        if redis:
            await redis.hset(f"job:{job_id}", mapping={
                "status": "in_progress",
                "progress": "10",
            })

        # Create user directory
        user_dir = REPORTS_DIR / user_id
        user_dir.mkdir(parents=True, exist_ok=True)

        # Process each file
        processed_files = []

        for i, (filename, content) in enumerate(zip(filenames, file_contents)):
            logger.debug(f"Processing file {i+1}/{len(filenames)}: {filename}")

            # Extract text based on file type
            ext = Path(filename).suffix.lower()
            text_content = ""

            if ext == ".pdf":
                text_content = await _extract_pdf_text(content)
            elif ext == ".docx":
                text_content = await _extract_docx_text(content)
            elif ext in (".txt", ".md"):
                text_content = content.decode("utf-8", errors="replace")
            else:
                logger.warning(f"Unknown file type: {ext}")
                text_content = content.decode("utf-8", errors="replace")

            # Save processed content
            output_path = user_dir / f"{job_id}_{Path(filename).stem}.txt"
            output_path.write_text(text_content)

            processed_files.append({
                "original_filename": filename,
                "output_path": str(output_path),
                "char_count": len(text_content),
                "word_count": len(text_content.split()),
            })

            # Update progress
            progress = 10 + int(80 * (i + 1) / len(filenames))
            if redis:
                await redis.hset(f"job:{job_id}", "progress", str(progress))

        # Finalize
        result_path = str(user_dir / job_id)

        if redis:
            await redis.hset(f"job:{job_id}", mapping={
                "status": "completed",
                "progress": "100",
                "result_path": result_path,
                "completed_at": datetime.now(timezone.utc).isoformat(),
            })

        logger.info(f"Upload job {job_id} completed: {len(processed_files)} files")

        return {
            "result_path": result_path,
            "files": processed_files,
        }

    except Exception as e:
        logger.exception(f"Upload job {job_id} failed")

        if redis:
            await redis.hset(f"job:{job_id}", mapping={
                "status": "failed",
                "error": str(e),
            })

        raise


async def _extract_pdf_text(content: bytes) -> str:
    """Extract text from PDF content."""
    try:
        import fitz  # PyMuPDF

        doc = fitz.open(stream=content, filetype="pdf")
        text_parts = []

        for page in doc:
            text_parts.append(page.get_text())

        doc.close()
        return "\n\n".join(text_parts)

    except ImportError:
        logger.warning("PyMuPDF not installed, falling back to basic extraction")
        return content.decode("utf-8", errors="replace")
    except Exception as e:
        logger.error(f"PDF extraction failed: {e}")
        return ""


async def _extract_docx_text(content: bytes) -> str:
    """Extract text from DOCX content."""
    try:
        from io import BytesIO
        from docx import Document

        doc = Document(BytesIO(content))
        text_parts = []

        for para in doc.paragraphs:
            text_parts.append(para.text)

        return "\n\n".join(text_parts)

    except ImportError:
        logger.warning("python-docx not installed, falling back to basic extraction")
        return content.decode("utf-8", errors="replace")
    except Exception as e:
        logger.error(f"DOCX extraction failed: {e}")
        return ""

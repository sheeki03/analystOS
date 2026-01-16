"""
Upload Middleware

Enforces max body size (50MB default) for file uploads via:
- Content-Length header check for early rejection
- Streaming byte count for actual enforcement (don't trust header alone)

This middleware is ALWAYS active in all environments:
- Dev/Uvicorn: This is the primary enforcement
- Prod with Nginx: Nginx client_max_body_size provides first line; this is backup
- Prod without proxy: This is the primary enforcement

Configuration via UPLOAD_MAX_BYTES env var (default: 50MB = 52428800 bytes)
"""

import logging
import os
from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send, Message

logger = logging.getLogger(__name__)

# Default 50MB
DEFAULT_MAX_BYTES = 50 * 1024 * 1024  # 50MB

# Allowed file extensions
ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt", ".md"}

# MIME types mapping (for validation with python-magic)
ALLOWED_MIME_TYPES = {
    "application/pdf": [".pdf"],
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [".docx"],
    "text/plain": [".txt", ".md"],
    "text/markdown": [".md"],
}


class UploadSizeLimitError(Exception):
    """Raised when upload size exceeds limit."""
    def __init__(self, size: int, max_size: int) -> None:
        self.size = size
        self.max_size = max_size
        super().__init__(
            f"Upload size {size} bytes exceeds maximum {max_size} bytes"
        )


class LimitUploadSizeMiddleware:
    """
    ASGI middleware to limit upload body size.

    Checks Content-Length header for early rejection, then counts actual
    bytes during streaming to prevent header spoofing attacks.

    Must be registered FIRST in the middleware stack for proper enforcement.
    """

    def __init__(
        self,
        app: ASGIApp,
        max_bytes: int | None = None,
    ) -> None:
        self.app = app
        self.max_bytes = max_bytes or int(
            os.getenv("UPLOAD_MAX_BYTES", DEFAULT_MAX_BYTES)
        )

    async def __call__(
        self,
        scope: Scope,
        receive: Receive,
        send: Send,
    ) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # Get Content-Length header if present
        headers = dict(scope.get("headers", []))
        content_length_header = headers.get(b"content-length")

        # Early rejection based on Content-Length header
        if content_length_header:
            try:
                content_length = int(content_length_header.decode())
                if content_length > self.max_bytes:
                    logger.warning(
                        f"Rejected upload: Content-Length {content_length} > {self.max_bytes}"
                    )
                    response = JSONResponse(
                        status_code=413,
                        content={
                            "detail": f"Request body too large. Maximum size is {self.max_bytes} bytes.",
                            "max_bytes": self.max_bytes,
                        },
                    )
                    await response(scope, receive, send)
                    return
            except (ValueError, UnicodeDecodeError):
                pass  # Invalid header, will count actual bytes

        # Wrap receive to count actual bytes
        bytes_received = 0
        body_too_large = False

        async def counting_receive() -> Message:
            nonlocal bytes_received, body_too_large

            message = await receive()

            if message["type"] == "http.request":
                body = message.get("body", b"")
                bytes_received += len(body)

                if bytes_received > self.max_bytes:
                    body_too_large = True
                    logger.warning(
                        f"Upload exceeded limit mid-stream: {bytes_received} > {self.max_bytes}"
                    )
                    # Return empty body to stop processing
                    # The error will be raised when the body is accessed
                    return {
                        "type": "http.request",
                        "body": b"",
                        "more_body": False,
                    }

            return message

        # Wrap send to intercept if body too large
        async def checking_send(message: Message) -> None:
            if body_too_large and message["type"] == "http.response.start":
                # Override with 413 response
                response = JSONResponse(
                    status_code=413,
                    content={
                        "detail": f"Request body too large. Maximum size is {self.max_bytes} bytes.",
                        "max_bytes": self.max_bytes,
                        "received_bytes": bytes_received,
                    },
                )
                await response(scope, receive, send)
                return
            await send(message)

        try:
            await self.app(scope, counting_receive, checking_send)
        except UploadSizeLimitError:
            response = JSONResponse(
                status_code=413,
                content={
                    "detail": f"Request body too large. Maximum size is {self.max_bytes} bytes.",
                    "max_bytes": self.max_bytes,
                },
            )
            await response(scope, receive, send)


def validate_file_extension(filename: str) -> bool:
    """Check if file extension is allowed."""
    if not filename:
        return False
    ext = os.path.splitext(filename)[1].lower()
    return ext in ALLOWED_EXTENSIONS


def validate_mime_type(file_content: bytes, filename: str) -> bool:
    """
    Validate file MIME type using python-magic.

    Requires libmagic system library:
    - macOS: brew install libmagic
    - Linux: apt install libmagic1

    Returns True if MIME type matches expected type for extension.
    Falls back to True if magic library not available.
    """
    try:
        import magic
    except ImportError:
        logger.warning("python-magic not installed, skipping MIME validation")
        return True

    ext = os.path.splitext(filename)[1].lower()

    try:
        # Detect MIME type from content
        detected_mime = magic.from_buffer(file_content[:2048], mime=True)

        # Check if detected MIME type allows this extension
        allowed_extensions = ALLOWED_MIME_TYPES.get(detected_mime, [])
        if ext not in allowed_extensions:
            logger.warning(
                f"MIME type mismatch: {filename} detected as {detected_mime}, "
                f"expected extensions: {allowed_extensions}"
            )
            return False

        return True

    except Exception as e:
        logger.error(f"MIME validation error: {e}")
        # Fail closed - reject on error
        return False


async def validate_upload_file(
    file_content: bytes,
    filename: str,
    max_bytes: int | None = None,
) -> tuple[bool, str | None]:
    """
    Comprehensive file upload validation.

    Checks:
    1. File size
    2. File extension
    3. MIME type (content sniffing)

    Returns:
        Tuple of (is_valid, error_message)
    """
    max_bytes = max_bytes or int(os.getenv("UPLOAD_MAX_BYTES", DEFAULT_MAX_BYTES))

    # Size check
    if len(file_content) > max_bytes:
        return False, f"File size {len(file_content)} exceeds maximum {max_bytes} bytes"

    # Extension check
    if not validate_file_extension(filename):
        return False, f"File extension not allowed. Allowed: {ALLOWED_EXTENSIONS}"

    # MIME type check
    if not validate_mime_type(file_content, filename):
        return False, "File content does not match expected type for extension"

    return True, None


# URL validation limits
MAX_URLS_PER_BATCH = 10
MAX_SITEMAP_URLS = 100


def validate_url_batch(urls: list[str]) -> tuple[bool, str | None]:
    """
    Validate a batch of URLs for scraping.

    Limits:
    - Max 10 URLs per batch request
    - URLs must be valid HTTP/HTTPS

    Returns:
        Tuple of (is_valid, error_message)
    """
    if len(urls) > MAX_URLS_PER_BATCH:
        return False, f"Maximum {MAX_URLS_PER_BATCH} URLs per batch"

    import validators
    for url in urls:
        if not validators.url(url):
            return False, f"Invalid URL: {url}"

    return True, None


def validate_sitemap_urls(urls: list[str]) -> tuple[bool, str | None]:
    """
    Validate URLs extracted from a sitemap.

    Limits:
    - Max 100 URLs from sitemap

    Returns:
        Tuple of (is_valid, error_message)
    """
    if len(urls) > MAX_SITEMAP_URLS:
        return False, f"Maximum {MAX_SITEMAP_URLS} URLs from sitemap"

    import validators
    for url in urls:
        if not validators.url(url):
            return False, f"Invalid URL from sitemap: {url}"

    return True, None

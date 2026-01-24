"""
Type definitions and serialization utilities for financial tools.

Matches Dexter's tools/types.ts interface exactly.
"""

import json
from typing import Any, List, Optional


def format_tool_result(data: Any, source_urls: Optional[List[str]] = None) -> str:
    """
    JSON serialization matching Dexter's formatToolResult EXACTLY.

    Note: Uses camelCase "sourceUrls" to match Dexter output.

    Args:
        data: The data to include in the result
        source_urls: Optional list of source URLs

    Returns:
        JSON string with data and optional sourceUrls (camelCase!)
    """
    result = {"data": data}
    if source_urls:
        result["sourceUrls"] = source_urls  # camelCase to match Dexter!
    return json.dumps(result)

"""
Automation Router

Notion automation endpoints:
- GET /automation/status - Connection status and last sync time
- GET /automation/queue - Pending research items from Notion
- POST /automation/trigger/{item_id} - Manually trigger research for an item
- GET /automation/history - Recent completions with scores

Integrates with existing Notion automation modules:
- notion_watcher.py - Monitors Notion for new items
- notion_research.py - Processes research requests
- notion_scorer.py - Scores completed research
- notion_writer.py - Writes results back to Notion
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

from src.models.auth_models import TokenPayload
from src.models.job_models import JobCreatedResponse, JobType
from src.routers.auth_router import get_current_user
from src.services.job_manager import (
    JobManagerBase,
    JobType as JMJobType,
    get_job_manager_instance,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/automation", tags=["Automation"])


# ============================================================================
# Models
# ============================================================================

class NotionConnectionStatus(BaseModel):
    """Notion connection status."""
    connected: bool
    workspace_name: Optional[str] = None
    database_id: Optional[str] = None
    last_sync: Optional[datetime] = None
    sync_interval_minutes: int = 5
    error: Optional[str] = None


class QueueItem(BaseModel):
    """Research queue item from Notion."""
    item_id: str
    title: str
    status: str
    priority: Optional[str] = None
    created_at: datetime
    source_type: Optional[str] = None  # "url", "document", etc.
    source_url: Optional[str] = None


class QueueResponse(BaseModel):
    """Queue response."""
    items: List[QueueItem]
    total: int


class TriggerResponse(BaseModel):
    """Manual trigger response."""
    job_id: str
    item_id: str
    message: str


class HistoryItem(BaseModel):
    """Completed research item."""
    item_id: str
    title: str
    completed_at: datetime
    score: Optional[float] = None
    score_breakdown: Optional[Dict[str, float]] = None
    report_id: Optional[str] = None
    duration_seconds: Optional[int] = None


class HistoryResponse(BaseModel):
    """History response."""
    items: List[HistoryItem]
    total: int


class WorkflowConfig(BaseModel):
    """Workflow configuration."""
    auto_process: bool = True
    default_model: str = "anthropic/claude-sonnet-4.5"
    auto_score: bool = True
    notify_on_complete: bool = False


# ============================================================================
# Dependencies
# ============================================================================

def get_job_manager() -> JobManagerBase:
    """Dependency to get job manager."""
    return get_job_manager_instance()


# ============================================================================
# Notion Integration (placeholders - integrate with existing modules)
# ============================================================================

async def get_notion_status() -> Dict[str, Any]:
    """Get Notion connection status."""
    # TODO: Integrate with existing notion_watcher.py
    # Check if Notion client is configured and connected
    import os

    notion_token = os.getenv("NOTION_TOKEN")
    database_id = os.getenv("NOTION_DATABASE_ID")

    if not notion_token or not database_id:
        return {
            "connected": False,
            "error": "Notion not configured. Set NOTION_TOKEN and NOTION_DATABASE_ID.",
        }

    # Placeholder - would actually test connection
    return {
        "connected": True,
        "workspace_name": "Research Workspace",
        "database_id": database_id[:8] + "...",
        "last_sync": datetime.now(timezone.utc),
        "sync_interval_minutes": 5,
    }


async def get_notion_queue() -> List[Dict[str, Any]]:
    """Get pending items from Notion queue."""
    # TODO: Integrate with existing notion_watcher.py
    # Placeholder data
    return [
        {
            "item_id": "notion-item-001",
            "title": "Research: Example Project",
            "status": "pending",
            "priority": "high",
            "created_at": datetime.now(timezone.utc),
            "source_type": "url",
            "source_url": "https://example.com/whitepaper",
        },
    ]


async def get_notion_history(limit: int = 20) -> List[Dict[str, Any]]:
    """Get recently completed items from Notion."""
    # TODO: Integrate with existing notion modules
    # Placeholder data
    return [
        {
            "item_id": "notion-item-000",
            "title": "Research: Completed Project",
            "completed_at": datetime.now(timezone.utc),
            "score": 85.5,
            "score_breakdown": {
                "technology": 90,
                "tokenomics": 80,
                "governance": 85,
                "team": 88,
                "market": 82,
            },
            "report_id": "report-uuid-000",
            "duration_seconds": 300,
        },
    ]


async def trigger_research(item_id: str, user_id: str) -> str:
    """Trigger research for a Notion item. Returns job_id."""
    job_manager = get_job_manager_instance()

    # TODO: Integrate with existing notion_research.py
    # For now, create a placeholder job

    async def _notion_research_job(job_id: str, item_id: str, user_id: str) -> str:
        """Process research for a Notion item."""
        await job_manager.update_progress(job_id, 10)
        # Placeholder - would actually process here
        await job_manager.update_progress(job_id, 100)
        return f"notion-result-{item_id}"

    job_id = await job_manager.create_job(
        user_id=user_id,
        job_type=JMJobType.GENERATE,
        func=_notion_research_job,
        item_id=item_id,
    )

    return job_id


# ============================================================================
# Endpoints
# ============================================================================

@router.get("/status", response_model=NotionConnectionStatus)
async def get_status(
    current_user: TokenPayload = Depends(get_current_user),
) -> NotionConnectionStatus:
    """
    Get Notion connection status.

    Returns connection state, workspace info, and last sync time.
    """
    status_data = await get_notion_status()
    return NotionConnectionStatus(**status_data)


@router.get("/queue", response_model=QueueResponse)
async def get_queue(
    limit: int = Query(20, ge=1, le=100),
    current_user: TokenPayload = Depends(get_current_user),
) -> QueueResponse:
    """
    Get pending research items from Notion queue.

    Returns items awaiting research processing.
    """
    items_data = await get_notion_queue()

    items = [QueueItem(**item) for item in items_data[:limit]]

    return QueueResponse(
        items=items,
        total=len(items_data),
    )


@router.post("/trigger/{item_id}", response_model=TriggerResponse)
async def trigger_item(
    item_id: str,
    current_user: TokenPayload = Depends(get_current_user),
) -> TriggerResponse:
    """
    Manually trigger research for a Notion item.

    Bypasses the automatic queue processing and starts immediately.
    Returns job_id to poll for status.
    """
    # Verify item exists in queue
    items = await get_notion_queue()
    item_exists = any(item["item_id"] == item_id for item in items)

    if not item_exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item {item_id} not found in queue",
        )

    # Trigger research
    job_id = await trigger_research(item_id, current_user.sub)

    logger.info(f"User {current_user.username} triggered research for item {item_id}")

    return TriggerResponse(
        job_id=job_id,
        item_id=item_id,
        message="Research triggered successfully",
    )


@router.get("/history", response_model=HistoryResponse)
async def get_history(
    limit: int = Query(20, ge=1, le=100),
    current_user: TokenPayload = Depends(get_current_user),
) -> HistoryResponse:
    """
    Get recent completed research items.

    Returns items with completion time, scores, and report links.
    """
    history_data = await get_notion_history(limit)

    items = [HistoryItem(**item) for item in history_data]

    return HistoryResponse(
        items=items,
        total=len(history_data),
    )


@router.get("/config", response_model=WorkflowConfig)
async def get_config(
    current_user: TokenPayload = Depends(get_current_user),
) -> WorkflowConfig:
    """
    Get current workflow configuration.
    """
    # TODO: Load from storage/database
    return WorkflowConfig()


@router.put("/config", response_model=WorkflowConfig)
async def update_config(
    config: WorkflowConfig,
    current_user: TokenPayload = Depends(get_current_user),
) -> WorkflowConfig:
    """
    Update workflow configuration.
    """
    # TODO: Save to storage/database
    logger.info(f"User {current_user.username} updated workflow config")
    return config


@router.post("/sync")
async def force_sync(
    current_user: TokenPayload = Depends(get_current_user),
) -> dict:
    """
    Force an immediate sync with Notion.

    Triggers the watcher to check for new items now instead of waiting
    for the next scheduled interval.
    """
    # TODO: Integrate with existing notion_watcher.py
    logger.info(f"User {current_user.username} triggered manual Notion sync")

    return {
        "message": "Sync triggered",
        "next_auto_sync_in_seconds": 300,
    }

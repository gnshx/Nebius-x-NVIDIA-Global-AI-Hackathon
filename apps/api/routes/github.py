"""RepoMedic — GitHub Webhook Route"""
from __future__ import annotations

import structlog
from fastapi import APIRouter, BackgroundTasks, Header, HTTPException, Request, status

from services.github.app import github_app
from services.github.webhook import dispatch_webhook

router = APIRouter()
logger = structlog.get_logger(__name__)


@router.post("/webhook", status_code=status.HTTP_200_OK)
async def github_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    x_github_event: str = Header(...),
    x_hub_signature_256: str = Header(default=""),
    x_github_delivery: str = Header(default=""),
) -> dict:
    """
    Receive GitHub webhook events.
    Verifies HMAC signature before processing.
    """
    body = await request.body()

    # Verify webhook signature
    if not github_app.verify_webhook_signature(body, x_hub_signature_256):
        logger.warning(
            "webhook_signature_invalid",
            event=x_github_event,
            delivery=x_github_delivery,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid webhook signature",
        )

    payload = await request.json()
    logger.info(
        "webhook_received",
        event=x_github_event,
        delivery=x_github_delivery,
        action=payload.get("action"),
    )

    result = await dispatch_webhook(x_github_event, payload)
    return result

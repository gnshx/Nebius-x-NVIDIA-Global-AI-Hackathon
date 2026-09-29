"""
RepoMedic — GitHub Webhook Event Dispatcher
"""
from __future__ import annotations

from typing import Any

import structlog

logger = structlog.get_logger(__name__)

REPOMEDIC_TRIGGER = "/repomedic fix"


async def dispatch_webhook(event_type: str, payload: dict[str, Any]) -> dict[str, Any]:
    """Route GitHub webhook events to appropriate handlers."""
    handlers = {
        "installation": handle_installation,
        "installation_repositories": handle_installation_repos,
        "issue_comment": handle_issue_comment,
        "issues": handle_issues,
    }
    handler = handlers.get(event_type)
    if handler:
        return await handler(payload)
    logger.debug("unhandled_webhook_event", event_type=event_type)
    return {"status": "ignored", "event": event_type}


async def handle_installation(payload: dict[str, Any]) -> dict[str, Any]:
    """Handle GitHub App installation events."""
    # TODO: persist installation to DB
    action = payload.get("action")
    logger.info("github_installation", action=action)
    return {"status": "ok", "action": action}


async def handle_installation_repos(payload: dict[str, Any]) -> dict[str, Any]:
    action = payload.get("action")
    logger.info("github_installation_repos", action=action)
    return {"status": "ok", "action": action}


async def handle_issue_comment(payload: dict[str, Any]) -> dict[str, Any]:
    """Trigger agent run when /repomedic fix is commented."""
    action = payload.get("action")
    if action != "created":
        return {"status": "ignored", "reason": "not a new comment"}

    comment_body = payload.get("comment", {}).get("body", "")
    if REPOMEDIC_TRIGGER not in comment_body:
        return {"status": "ignored", "reason": "trigger phrase not found"}

    repo_full_name = payload["repository"]["full_name"]
    issue_number = payload["issue"]["number"]
    installation_id = payload["installation"]["id"]

    logger.info(
        "repomedic_triggered",
        repo=repo_full_name,
        issue=issue_number,
        installation_id=installation_id,
    )

    # Import here to avoid circular imports
    from celery_app import start_agent_run_task

    task = start_agent_run_task.delay(
        repository_full_name=repo_full_name,
        issue_number=issue_number,
        installation_id=installation_id,
        triggered_by="webhook",
    )
    return {"status": "triggered", "task_id": task.id, "issue": issue_number}


async def handle_issues(payload: dict[str, Any]) -> dict[str, Any]:
    action = payload.get("action")
    logger.info("github_issue_event", action=action)
    return {"status": "ok", "action": action}

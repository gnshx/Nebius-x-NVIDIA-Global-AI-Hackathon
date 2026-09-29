"""
RepoMedic — Server-Sent Events (SSE) Route

Streams real-time run updates to the frontend.
Subscribes to Redis pub/sub channel for the given run_id.
"""
from __future__ import annotations

import asyncio
import json
import uuid

import structlog
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse

router = APIRouter()
logger = structlog.get_logger(__name__)

HEARTBEAT_INTERVAL = 15  # seconds


@router.get("/{run_id}/events")
async def run_events(run_id: str, request: Request) -> StreamingResponse:
    """
    Stream run events via Server-Sent Events.
    
    Connect: GET /api/runs/{run_id}/events
    
    Event types:
    - step_started    { step_type, step_id, iteration }
    - step_completed  { step_type, step_id, duration }
    - step_failed     { step_type, step_id, error }
    - run_completed   { pr_url }
    - run_failed      { error }
    - heartbeat       {}
    """
    try:
        uuid.UUID(run_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid run ID")

    async def event_generator():
        from agents.nodes.base import get_redis
        redis = get_redis()
        pubsub = redis.pubsub()
        await pubsub.subscribe(f"run:{run_id}")

        try:
            yield f"data: {json.dumps({'type': 'connected', 'run_id': run_id})}\n\n"

            while True:
                # Check if client disconnected
                if await request.is_disconnected():
                    logger.info("sse_client_disconnected", run_id=run_id)
                    break

                # Try to get a message (non-blocking with timeout)
                try:
                    message = await asyncio.wait_for(
                        pubsub.get_message(ignore_subscribe_messages=True),
                        timeout=HEARTBEAT_INTERVAL,
                    )
                except asyncio.TimeoutError:
                    # Send heartbeat to keep connection alive
                    yield f"data: {json.dumps({'type': 'heartbeat'})}\n\n"
                    continue

                if message and message["type"] == "message":
                    data = message["data"]
                    yield f"data: {data}\n\n"

                    # Check if this is a terminal event
                    try:
                        parsed = json.loads(data)
                        if parsed.get("type") in ("run_completed", "run_failed"):
                            # Send one final event and close
                            await asyncio.sleep(0.1)
                            break
                    except json.JSONDecodeError:
                        pass

                await asyncio.sleep(0.05)

        finally:
            await pubsub.unsubscribe(f"run:{run_id}")
            await pubsub.close()
            logger.info("sse_connection_closed", run_id=run_id)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
            "Connection": "keep-alive",
        },
    )

"""
RepoMedic — FastAPI Application Entry Point
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config import settings
from db.database import init_db, close_db
from routes import github, health, repositories, runs, events

# ---------------------------------------------------------------------------
# Structured logging setup
# ---------------------------------------------------------------------------
structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.dev.ConsoleRenderer() if settings.is_development else structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.make_filtering_bound_logger(
        getattr(logging, settings.log_level)
    ),
)

logger = structlog.get_logger(__name__)


# ---------------------------------------------------------------------------
# Application lifespan
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Initialize and teardown application resources."""
    logger.info(
        "startup",
        env=settings.app_env.value,
        max_fix_iterations=settings.max_fix_iterations,
    )
    await init_db()
    yield
    await close_db()
    logger.info("shutdown")


# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------
app = FastAPI(
    title="RepoMedic API",
    description=(
        "Autonomous GitHub Issue-to-PR Agent powered by NVIDIA Nemotron "
        "on Nebius Token Factory"
    ),
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        settings.next_public_app_url,
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Global exception handler
# ---------------------------------------------------------------------------
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error(
        "unhandled_exception",
        path=request.url.path,
        method=request.method,
        error=str(exc),
        exc_info=True,
    )
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "type": type(exc).__name__},
    )


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
app.include_router(health.router, tags=["Health"])
app.include_router(github.router, prefix="/api/github", tags=["GitHub"])
app.include_router(runs.router, prefix="/api/runs", tags=["Runs"])
app.include_router(events.router, prefix="/api/runs", tags=["Events"])
app.include_router(repositories.router, prefix="/api/repositories", tags=["Repositories"])


@app.get("/", include_in_schema=False)
async def root() -> dict[str, str]:
    return {
        "service": "RepoMedic API",
        "version": "0.1.0",
        "docs": "/docs",
    }

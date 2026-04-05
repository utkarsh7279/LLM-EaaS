"""FastAPI application entrypoint."""

from __future__ import annotations

import asyncio
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers.experiments import router as experiments_router
from app.core.config import get_settings
from app.db.session import async_engine
from app.models.db_models import Base
from app.utils.logging import configure_logging


def create_app() -> FastAPI:
    """Create and configure the FastAPI app."""
    configure_logging()
    settings = get_settings()
    logger = logging.getLogger(__name__)

    app = FastAPI(title="LLM Evaluation-as-a-Service")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Routers are thin; business logic lives in services for testability.
    app.include_router(experiments_router, prefix="/experiments", tags=["experiments"])

    @app.on_event("startup")
    async def initialize_database_schema() -> None:
        """Create required tables on boot for managed deployments."""
        max_retries = 5
        retry_delay_seconds = 2

        for attempt in range(1, max_retries + 1):
            try:
                async with async_engine.begin() as connection:
                    await connection.run_sync(Base.metadata.create_all)
                logger.info("Database schema initialized successfully")
                return
            except Exception as exc:
                if attempt == max_retries:
                    logger.exception("Database schema initialization failed after retries")
                    raise

                logger.warning(
                    "Database schema initialization failed on attempt %s/%s: %s",
                    attempt,
                    max_retries,
                    exc,
                )
                await asyncio.sleep(retry_delay_seconds)

    @app.get("/")
    def root() -> dict[str, str]:
        """Root endpoint for quick service checks in a browser."""
        return {
            "service": "LLM Evaluation-as-a-Service",
            "status": "ok",
            "health": "/health",
            "docs": "/docs",
        }

    @app.get("/health")
    def health_check() -> dict[str, str]:
        """Simple health check endpoint."""
        return {"status": "ok"}

    return app


app = create_app()

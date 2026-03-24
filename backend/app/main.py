"""FastAPI application entrypoint."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers.experiments import router as experiments_router
from app.core.config import get_settings
from app.utils.logging import configure_logging


def create_app() -> FastAPI:
    """Create and configure the FastAPI app."""
    configure_logging()
    settings = get_settings()

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

    @app.get("/health")
    def health_check() -> dict[str, str]:
        """Simple health check endpoint."""
        return {"status": "ok"}

    return app


app = create_app()

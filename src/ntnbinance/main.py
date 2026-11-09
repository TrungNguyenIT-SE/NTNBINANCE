"""FastAPI application factory and local development entry point."""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI
from uvicorn import run as uvicorn_run

from ntnbinance import __version__
from ntnbinance.config import Settings, load_settings


def create_app(settings: Settings | None = None) -> FastAPI:
    """Create a side-effect-light app suitable for tests and local execution."""

    active = settings or load_settings()
    app = FastAPI(
        title="NTN Binance Signal Research",
        version=__version__,
        debug=active.debug,
        docs_url="/docs" if active.debug else None,
        redoc_url=None,
    )
    app.state.settings = active

    @app.get("/health/live", tags=["health"])
    def live() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/health/ready", tags=["health"])
    def ready() -> dict[str, str]:
        return {"status": "ready", "profile": active.profile}

    @app.get("/api/v1/meta", tags=["meta"])
    def metadata() -> dict[str, Any]:
        return {
            "name": "ntnbinance",
            "version": __version__,
            "profile": active.profile,
            "scope": "local-private-research",
            "trading_enabled": False,
        }

    return app


app = create_app()


def run() -> None:
    """Start the API with the selected safe local profile."""

    settings = load_settings()
    uvicorn_run(
        "ntnbinance.main:app",
        host=settings.host,
        port=settings.port,
        workers=settings.workers,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    run()

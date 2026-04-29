"""FastAPI entry-point for wupbro."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import __version__
from .routers import dashboard, drivers, events, notifications


def create_app() -> FastAPI:
    app = FastAPI(
        title="WUP Browser Dashboard",
        version=__version__,
        description=(
            "Backend for the WUP regression watcher. Receives events from "
            "WUP agents (REGRESSION, PASS, ANOMALY, VISUAL_DIFF, HEALTH_TRANSITION), "
            "exposes drivers (DOM diff, browserless, anomaly), and serves a dashboard."
        ),
    )

    # Permissive CORS — dashboard usually served from same origin, but agents
    # may live elsewhere. Tighten in production.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(events.router)
    app.include_router(drivers.router)
    app.include_router(dashboard.router)
    app.include_router(notifications.router)

    @app.get("/healthz", tags=["meta"])
    async def healthz():
        return {"ok": True, "version": __version__}

    return app


# Module-level instance for `uvicorn wupbro.main:app`
app = create_app()

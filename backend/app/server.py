from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from .main import app as agent_app
from .async_agent_routes import router as async_agent_router
from .runtime_routes import router as runtime_router
from ..system_backends import router as backend_router, shutdown_backends, startup_backends


def _remove_legacy_agent_run_route() -> None:
    agent_app.router.routes[:] = [
        route for route in agent_app.router.routes
        if not (getattr(route, "path", None) == "/api/agent/run" and "POST" in getattr(route, "methods", set()))
    ]


_remove_legacy_agent_run_route()
agent_app.include_router(async_agent_router)
agent_app.include_router(runtime_router)
agent_app.include_router(backend_router)


@asynccontextmanager
async def lifespan(_: FastAPI):
    await startup_backends()
    try:
        yield
    finally:
        await shutdown_backends()


agent_app.router.lifespan_context = lifespan
app = agent_app


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.server:app", host="127.0.0.1", port=8000, reload=False)

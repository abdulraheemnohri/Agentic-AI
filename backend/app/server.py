from __future__ import annotations

from contextlib import asynccontextmanager
from fastapi import FastAPI

from .main import app as agent_app
from .async_agent_routes import router as async_agent_router
from .runtime_routes import router as runtime_router
from .runtime_control_routes import router as observability_router, configure as configure_observability
from .security_routes import router as security_router, health as system1_health
from . import main as core
from ..system_backends import router as backend_router, shutdown_backends, startup_backends


def _remove_legacy_agent_run_route() -> None:
    agent_app.router.routes[:] = [r for r in agent_app.router.routes if not (getattr(r, "path", None) == "/api/agent/run" and "POST" in getattr(r, "methods", set()))]

_remove_legacy_agent_run_route()
configure_observability(str(core.store.db_path))
agent_app.include_router(async_agent_router)
agent_app.include_router(runtime_router)
agent_app.include_router(observability_router)
agent_app.include_router(security_router)
agent_app.include_router(backend_router)


def _system1_check() -> bool:
    return bool(getattr(core, "agent_kernel", None) and getattr(core, "store", None))

system1_health.bind(_system1_check)

@asynccontextmanager
async def lifespan(_: FastAPI):
    await startup_backends()
    await system1_health.start()
    try:
        yield
    finally:
        await system1_health.shutdown()
        await shutdown_backends()

agent_app.router.lifespan_context = lifespan
app = agent_app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.server:app", host="127.0.0.1", port=8000, reload=False)

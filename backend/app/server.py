from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from .main import app as agent_app
from ..system_backends import router as backend_router, shutdown_backends, startup_backends


@asynccontextmanager
async def lifespan(_: FastAPI):
    await startup_backends()
    try:
        yield
    finally:
        await shutdown_backends()


# Reuse the existing Agentic-AI application and add the two-backend control plane.
agent_app.include_router(backend_router)
agent_app.router.lifespan_context = lifespan
app = agent_app


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("backend.app.server:app", host="127.0.0.1", port=8000, reload=False)

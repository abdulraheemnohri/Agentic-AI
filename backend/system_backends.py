from __future__ import annotations

from typing import Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from .system1.service import System1AutomaticBackend
from .system2.service import System2LifecycleBackend

router = APIRouter(prefix="/api/backends", tags=["backends"])
system1_backend = System1AutomaticBackend()
system2_backend = System2LifecycleBackend()

class System2Start(BaseModel):
    runtime_module: str | None = None

class System2Update(BaseModel):
    package: str | None = None

class System2Upgrade(BaseModel):
    version: str = Field(min_length=1, max_length=64)
    local_path: str | None = None

@router.get("/status")
async def backend_status():
    return {"system1": system1_backend.status(), "system2": system2_backend.status(), "frontend": {"control": "system2_only"}}

@router.get("/system1")
async def system1_status():
    return system1_backend.status()

@router.get("/system2")
async def system2_status():
    return system2_backend.status()

@router.post("/system2/start")
async def system2_start(request: System2Start):
    try: return await system2_backend.start(request.runtime_module)
    except ValueError as exc: raise HTTPException(422, str(exc)) from exc

@router.post("/system2/stop")
async def system2_stop():
    return await system2_backend.stop()

@router.post("/system2/restart")
async def system2_restart():
    return await system2_backend.restart()

@router.post("/system2/update")
async def system2_update(request: System2Update):
    try: return await system2_backend.update(request.package)
    except ValueError as exc: raise HTTPException(422, str(exc)) from exc

@router.post("/system2/upgrade")
async def system2_upgrade(request: System2Upgrade):
    try: return await system2_backend.upgrade(request.version, request.local_path)
    except ValueError as exc: raise HTTPException(422, str(exc)) from exc

async def startup_backends() -> None:
    # System 1 is mandatory and starts automatically with the application.
    system1_backend.start()

async def shutdown_backends() -> None:
    await system1_backend.shutdown()
    await system2_backend.stop()

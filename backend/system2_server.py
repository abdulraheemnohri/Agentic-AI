"""Dedicated System 2 backend process.

Run with: uvicorn backend.system2_server:app --host 127.0.0.1 --port 8102
The frontend may start, stop, update and upgrade this local runtime.
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from .system2.service import System2LifecycleBackend

backend = System2LifecycleBackend()
app = FastAPI(title="Agentic-AI System 2 Backend", version="1.0.0")

class StartRequest(BaseModel):
    runtime_module: str | None = None
class UpdateRequest(BaseModel):
    package: str | None = None
class UpgradeRequest(BaseModel):
    version: str = Field(min_length=1, max_length=64)
    local_path: str | None = None

@app.get("/health")
async def health(): return backend.status()

@app.post("/control/start")
async def start(request: StartRequest):
    try: return await backend.start(request.runtime_module)
    except ValueError as exc: raise HTTPException(422, str(exc)) from exc

@app.post("/control/stop")
async def stop(): return await backend.stop()

@app.post("/control/restart")
async def restart(): return await backend.restart()

@app.post("/control/update")
async def update(request: UpdateRequest):
    try: return await backend.update(request.package)
    except ValueError as exc: raise HTTPException(422, str(exc)) from exc

@app.post("/control/upgrade")
async def upgrade(request: UpgradeRequest):
    try: return await backend.upgrade(request.version, request.local_path)
    except ValueError as exc: raise HTTPException(422, str(exc)) from exc

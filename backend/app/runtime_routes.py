from __future__ import annotations

import asyncio
import json
from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from . import main as core
from .async_agent_routes import active_run_ids
from .runtime import runtime

router = APIRouter(prefix="/api/runtime", tags=["runtime"])


class RuntimeConfigUpdate(BaseModel):
    max_concurrency: int | None = Field(default=None, ge=1, le=16)
    queue_limit: int | None = Field(default=None, ge=1, le=500)
    poll_interval_ms: int | None = Field(default=None, ge=100, le=5000)


@router.get("/status")
def runtime_status() -> dict[str, Any]:
    return runtime.status()


@router.get("/config")
def runtime_config() -> dict[str, Any]:
    return {"config": runtime.status()["config"]}


@router.put("/config")
def update_runtime_config(request: RuntimeConfigUpdate) -> dict[str, Any]:
    changes = {k: v for k, v in request.model_dump().items() if v is not None}
    return {"config": runtime.save_config(**changes).__dict__}


@router.get("/active")
def active_runs() -> dict[str, Any]:
    return {"count": len(active_run_ids()), "run_ids": sorted(active_run_ids())}


@router.get("/events/{run_id}")
async def run_events(run_id: str):
    run = core.agent_runs.get(run_id) or core.store.get_agent_run(run_id)
    if not run:
        raise HTTPException(404, "agent_run_not_found")

    async def stream():
        sent = 0
        idle = 0
        while idle < 20:
            current = core.agent_runs.get(run_id) or core.store.get_agent_run(run_id) or run
            events = current.get("stream", []) if isinstance(current, dict) else []
            if len(events) > sent:
                for event in events[sent:]:
                    yield f"data: {json.dumps(event, separators=(',', ':'))}\n\n"
                sent = len(events)
                idle = 0
            else:
                idle += 1
            status = current.get("status") if isinstance(current, dict) else None
            if status in {"completed", "failed", "escalated", "cancelled"} and idle >= 2:
                break
            await asyncio.sleep(runtime.config.poll_interval_ms / 1000)
        yield "event: end\ndata: {}\n\n"

    return StreamingResponse(stream(), media_type="text/event-stream", headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})

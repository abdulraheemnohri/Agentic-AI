from __future__ import annotations

import asyncio
from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse

from .recovery import RecoveryManager
from .runtime_observability import bus

router = APIRouter(prefix="/api/observability", tags=["observability"])
_recovery: RecoveryManager | None = None


def configure(db_path: str) -> None:
    global _recovery
    _recovery = RecoveryManager(db_path)


def recovery() -> RecoveryManager:
    if _recovery is None:
        raise RuntimeError("observability_not_configured")
    return _recovery


@router.get("/audit")
def audit(limit: int = Query(200, ge=1, le=1000)):
    return {"events": recovery().audit_list(limit)}


@router.get("/recovery")
def recoverable_runs():
    return {"runs": recovery().recoverable()}


@router.get("/events")
async def events():
    async def stream():
        yield "event: connected\ndata: {\"ok\":true}\n\n"
        async for event in bus.subscribe():
            yield bus.sse(event)
    return StreamingResponse(stream(), media_type="text/event-stream", headers={"Cache-Control":"no-cache","X-Accel-Buffering":"no"})


@router.get("/health")
def observability_health():
    return {"ok": True, "transport": "sse", "audit": _recovery is not None}

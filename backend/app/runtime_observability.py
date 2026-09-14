from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from typing import Any


class RuntimeEventBus:
    """In-process fan-out bus used by SSE/WebSocket-compatible clients."""
    def __init__(self) -> None:
        self._subscribers: set[asyncio.Queue[dict[str, Any]]] = set()

    def publish(self, event: dict[str, Any]) -> None:
        payload = {"timestamp": datetime.now(timezone.utc).isoformat(), **event}
        for q in list(self._subscribers):
            if q.full():
                try: q.get_nowait()
                except asyncio.QueueEmpty: pass
            try: q.put_nowait(payload)
            except asyncio.QueueFull: pass

    async def subscribe(self):
        q: asyncio.Queue[dict[str, Any]] = asyncio.Queue(maxsize=256)
        self._subscribers.add(q)
        try:
            while True:
                yield await q.get()
        finally:
            self._subscribers.discard(q)

    @staticmethod
    def sse(event: dict[str, Any]) -> str:
        return "event: runtime\ndata: " + json.dumps(event, default=str) + "\n\n"


bus = RuntimeEventBus()

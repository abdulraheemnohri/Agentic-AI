from __future__ import annotations

from copy import deepcopy
from typing import Any


class Observer:
    """In-memory execution observation store for the current V1 runtime."""

    def __init__(self) -> None:
        self._events: dict[str, list[dict[str, Any]]] = {}

    def emit(self, task_id: str, event_type: str, **payload: Any) -> dict[str, Any]:
        from datetime import datetime, timezone

        event = {
            "type": event_type,
            "at": datetime.now(timezone.utc).isoformat(),
            **payload,
        }
        self._events.setdefault(task_id, []).append(event)
        return deepcopy(event)

    def list(self, task_id: str) -> list[dict[str, Any]]:
        return deepcopy(self._events.get(task_id, []))

    def clear(self, task_id: str) -> None:
        self._events.pop(task_id, None)


observer = Observer()

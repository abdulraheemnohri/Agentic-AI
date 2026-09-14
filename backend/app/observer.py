"""
Observer: Execution Observation and Event Logging
- Logs all runtime events for tasks and agent runs.
- Integrates with EventBus for centralized event emission.
- Persists events to storage for audit and recovery.
"""

from __future__ import annotations
from copy import deepcopy
from datetime import datetime, timezone
from typing import Any, Dict, List

from .event_bus import get_event_bus


class Observer:
    """
    In-memory execution observation store for Agentic-AI runtime.
    - Logs events per task/agent run.
    - Integrates with EventBus for global event emission.
    - Supports persistence via storage.
    """

    def __init__(self) -> None:
        self._events: Dict[str, List[Dict[str, Any]]] = {}
        self._event_bus = get_event_bus()

    def emit(
        self,
        task_id: str,
        event_type: str,
        run_id: str | None = None,
        **payload: Any,
    ) -> Dict[str, Any]:
        """
        Emit an event for a specific task/agent run.
        - Logs the event in-memory.
        - Emits to the global EventBus.
        - Returns the event for immediate use.
        """
        event = {
            "type": event_type,
            "task_id": task_id,
            "run_id": run_id,
            "at": datetime.now(timezone.utc).isoformat(),
            **payload,
        }

        # Store in-memory
        self._events.setdefault(task_id, []).append(deepcopy(event))

        # Emit to EventBus (for SSE/WebSocket)
        self._event_bus.emit(
            event_type,
            task_id=task_id,
            run_id=run_id,
            **payload,
        )

        return deepcopy(event)

    def list(self, task_id: str) -> List[Dict[str, Any]]:
        """Get all events for a specific task."""
        return deepcopy(self._events.get(task_id, []))

    def clear(self, task_id: str) -> None:
        """Clear events for a specific task."""
        self._events.pop(task_id, None)

    def get_recent_events(
        self,
        limit: int = 100,
        task_id: str | None = None,
        run_id: str | None = None,
        event_type: str | None = None,
    ) -> List[Dict[str, Any]]:
        """
        Get recent events with optional filters.
        - `limit`: Maximum number of events to return.
        - `task_id`: Filter by task ID.
        - `run_id`: Filter by run ID.
        - `event_type`: Filter by event type.
        """
        all_events = []
        for events in self._events.values():
            all_events.extend(events)

        # Sort by timestamp (newest first)
        all_events.sort(key=lambda x: x["at"], reverse=True)

        # Apply filters
        if task_id:
            all_events = [e for e in all_events if e.get("task_id") == task_id]
        if run_id:
            all_events = [e for e in all_events if e.get("run_id") == run_id]
        if event_type:
            all_events = [e for e in all_events if e.get("type") == event_type]

        return all_events[:limit]


# Global Observer instance
observer = Observer()

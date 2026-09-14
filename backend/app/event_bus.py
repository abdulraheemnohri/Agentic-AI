"""
EventBus: Centralized Event System for Agentic-AI
- Emits events for all runtime state transitions.
- Supports SSE and WebSocket for real-time updates.
- Integrates with Observer for persistence.
"""

from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional
from uuid import uuid4
import asyncio
import json


class EventBus:
    """
    Centralized event bus for Agentic-AI runtime.
    - Emits events for all state transitions.
    - Supports multiple listeners (SSE, WebSocket, logging).
    - Integrates with Observer for persistence.
    """

    def __init__(self):
        self._listeners: List[Callable[[Dict[str, Any]], None]] = []
        self._event_history: List[Dict[str, Any]] = []
        self._max_history: int = 1000  # Keep last 1000 events in memory

    def add_listener(self, listener: Callable[[Dict[str, Any]], None]) -> None:
        """Add a listener to the event bus."""
        self._listeners.append(listener)

    def remove_listener(self, listener: Callable[[Dict[str, Any]], None]) -> None:
        """Remove a listener from the event bus."""
        if listener in self._listeners:
            self._listeners.remove(listener)

    def emit(self, event_type: str, **payload: Any) -> str:
        """
        Emit an event to all listeners.
        - Generates a unique event_id.
        - Adds timestamp and event_type to payload.
        - Stores in history (bounded).
        - Calls all listeners asynchronously.
        """
        event_id = str(uuid4())
        timestamp = datetime.now(timezone.utc).isoformat()
        event = {
            "event_id": event_id,
            "timestamp": timestamp,
            "event_type": event_type,
            **payload,
        }

        # Store in history (bounded)
        self._event_history.append(event)
        if len(self._event_history) > self._max_history:
            self._event_history = self._event_history[-self._max_history:]

        # Notify all listeners
        for listener in self._listeners:
            try:
                listener(event)
            except Exception as e:
                print(f"EventBus listener error: {e}")

        return event_id

    def get_history(
        self,
        limit: int = 100,
        event_type: Optional[str] = None,
        run_id: Optional[str] = None,
        task_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get event history with optional filters.
        - `limit`: Maximum number of events to return.
        - `event_type`: Filter by event type (e.g., 'task_created').
        - `run_id`: Filter by run ID.
        - `task_id`: Filter by task ID.
        """
        events = self._event_history[-limit:]

        if event_type:
            events = [e for e in events if e["event_type"] == event_type]
        if run_id:
            events = [e for e in events if e.get("run_id") == run_id]
        if task_id:
            events = [e for e in events if e.get("task_id") == task_id]

        return events

    def clear_history(self) -> None:
        """Clear event history."""
        self._event_history = []


# Global EventBus instance
_event_bus = EventBus()


def get_event_bus() -> EventBus:
    """Get the global EventBus instance."""
    return _event_bus


# --- Event Types ---
# Define all possible event types for type safety
EVENT_TYPES = {
    # Task events
    "task_created": "Task created",
    "task_updated": "Task updated",
    "task_completed": "Task completed",
    "task_failed": "Task failed",
    "task_cancelled": "Task cancelled",
    "task_escalated": "Task escalated",
    
    # Plan events
    "plan_created": "Plan created",
    "plan_updated": "Plan updated",
    "plan_validated": "Plan validated",
    "plan_replanned": "Plan replanned",
    
    # System 2 events
    "system2_started": "System 2 started",
    "system2_stopped": "System 2 stopped",
    "system2_proposal": "System 2 proposal generated",
    
    # System 1 events
    "system1_review": "System 1 review",
    "council_decision": "Council decision",
    "permission_granted": "Permission granted",
    "permission_denied": "Permission denied",
    
    # Runtime events
    "job_queued": "Job queued",
    "execution_started": "Execution started",
    "execution_output": "Execution output",
    "execution_failed": "Execution failed",
    
    # Verification events
    "verification_started": "Verification started",
    "verification_completed": "Verification completed",
    
    # Evaluation events
    "evaluation_completed": "Evaluation completed",
    
    # Recovery events
    "retry_started": "Retry started",
    "replan_started": "Replan started",
    "recovery_started": "Recovery started",
    "recovery_completed": "Recovery completed",
    
    # Security events
    "security_violation": "Security violation",
}


# --- Helper Functions ---

def emit_task_created(task_id: str, goal: str, autonomy: int) -> str:
    """Emit a task_created event."""
    return _event_bus.emit(
        "task_created",
        task_id=task_id,
        goal=goal,
        autonomy=autonomy,
    )


def emit_plan_created(task_id: str, plan_version: int, step_count: int) -> str:
    """Emit a plan_created event."""
    return _event_bus.emit(
        "plan_created",
        task_id=task_id,
        plan_version=plan_version,
        step_count=step_count,
    )


def emit_system2_proposal(
    task_id: str,
    run_id: str,
    proposal: Dict[str, Any],
) -> str:
    """Emit a system2_proposal event."""
    return _event_bus.emit(
        "system2_proposal",
        task_id=task_id,
        run_id=run_id,
        proposal=proposal,
    )


def emit_council_decision(
    task_id: str,
    run_id: str,
    decision: str,
    allowed: bool,
    votes: Dict[str, Any],
) -> str:
    """Emit a council_decision event."""
    return _event_bus.emit(
        "council_decision",
        task_id=task_id,
        run_id=run_id,
        decision=decision,
        allowed=allowed,
        votes=votes,
    )


def emit_permission_granted(
    task_id: str,
    run_id: str,
    tool: str,
) -> str:
    """Emit a permission_granted event."""
    return _event_bus.emit(
        "permission_granted",
        task_id=task_id,
        run_id=run_id,
        tool=tool,
    )


def emit_permission_denied(
    task_id: str,
    run_id: str,
    tool: str,
    reason: str,
) -> str:
    """Emit a permission_denied event."""
    return _event_bus.emit(
        "permission_denied",
        task_id=task_id,
        run_id=run_id,
        tool=tool,
        reason=reason,
    )


def emit_execution_started(
    task_id: str,
    run_id: str,
    step_id: str,
    tool: str,
) -> str:
    """Emit an execution_started event."""
    return _event_bus.emit(
        "execution_started",
        task_id=task_id,
        run_id=run_id,
        step_id=step_id,
        tool=tool,
    )


def emit_execution_output(
    task_id: str,
    run_id: str,
    step_id: str,
    output: Any,
) -> str:
    """Emit an execution_output event."""
    return _event_bus.emit(
        "execution_output",
        task_id=task_id,
        run_id=run_id,
        step_id=step_id,
        output=output,
    )


def emit_execution_failed(
    task_id: str,
    run_id: str,
    step_id: str,
    error: str,
) -> str:
    """Emit an execution_failed event."""
    return _event_bus.emit(
        "execution_failed",
        task_id=task_id,
        run_id=run_id,
        step_id=step_id,
        error=error,
    )


def emit_verification_completed(
    task_id: str,
    run_id: str,
    passed: bool,
    method: str,
) -> str:
    """Emit a verification_completed event."""
    return _event_bus.emit(
        "verification_completed",
        task_id=task_id,
        run_id=run_id,
        passed=passed,
        method=method,
    )


def emit_evaluation_completed(
    task_id: str,
    run_id: str,
    score: float,
    confidence: float,
) -> str:
    """Emit an evaluation_completed event."""
    return _event_bus.emit(
        "evaluation_completed",
        task_id=task_id,
        run_id=run_id,
        score=score,
        confidence=confidence,
    )


def emit_recovery_started(
    task_id: str,
    run_id: str,
    recovery_type: str,
) -> str:
    """Emit a recovery_started event."""
    return _event_bus.emit(
        "recovery_started",
        task_id=task_id,
        run_id=run_id,
        recovery_type=recovery_type,
    )


def emit_security_violation(
    actor: str,
    action: str,
    reason: str,
    risk: str = "HIGH",
) -> str:
    """Emit a security_violation event."""
    return _event_bus.emit(
        "security_violation",
        actor=actor,
        action=action,
        reason=reason,
        risk=risk,
    )

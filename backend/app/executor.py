from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime, timezone
from time import perf_counter
from typing import Any, Callable

from .observer import Observer
from .tool_registry import authorization


@dataclass
class ExecutionContext:
    task_id: str
    step_id: str
    tool_name: str
    autonomy: int
    approved: bool
    timeout_seconds: int
    attempt: int = 1


@dataclass
class ExecutionResult:
    status: str
    output: Any = None
    error: str | None = None
    duration_ms: int = 0
    started_at: str = ""
    finished_at: str = ""
    attempts: int = 1


class ExecutionCancelled(Exception):
    pass


class Executor:
    def __init__(self, observer: Observer, now_fn: Callable[[], str]) -> None:
        self.observer = observer
        self.now_fn = now_fn
        self._cancelled: set[str] = set()

    def cancel(self, task_id: str) -> None:
        self._cancelled.add(task_id)
        self.observer.emit(task_id, "execution_cancel_requested")

    def is_cancelled(self, task_id: str) -> bool:
        return task_id in self._cancelled

    def reset(self, task_id: str) -> None:
        self._cancelled.discard(task_id)

    async def _dispatch(self, tool: str, goal: str) -> dict[str, Any]:
        # V1 intentionally keeps execution local and deterministic.
        if tool == "clock":
            return {"utc": self.now_fn()}
        if tool == "echo":
            return {"text": goal}
        raise ValueError(f"unsupported_tool:{tool}")

    async def execute_step(
        self,
        task: dict[str, Any],
        step: dict[str, Any],
        approved: bool = False,
    ) -> ExecutionResult:
        task_id = task["id"]
        step_id = step["id"]
        tool = step["tool"]
        timeout = max(1, int(step.get("timeout_seconds", 30)))
        max_attempts = max(1, int(step.get("retry_count", 0)) + 1)
        last_error: str | None = None
        started_all = self.now_fn()
        total_start = perf_counter()

        for attempt in range(1, max_attempts + 1):
            if self.is_cancelled(task_id):
                return ExecutionResult("cancelled", error="execution_cancelled", attempts=attempt - 1)

            allowed, reason = authorization(tool, task["autonomy"], approved)
            if not allowed:
                self.observer.emit(task_id, "step_blocked", step_id=step_id, tool=tool, reason=reason, attempt=attempt)
                return ExecutionResult("blocked", error=reason, attempts=attempt)

            started = self.now_fn()
            self.observer.emit(task_id, "step_started", step_id=step_id, tool=tool, attempt=attempt)
            try:
                output = await asyncio.wait_for(self._dispatch(tool, task["goal"]), timeout=timeout)
                duration = int((perf_counter() - total_start) * 1000)
                finished = self.now_fn()
                self.observer.emit(task_id, "step_completed", step_id=step_id, tool=tool, attempt=attempt, duration_ms=duration, output=output)
                return ExecutionResult("completed", output=output, duration_ms=duration, started_at=started_all, finished_at=finished, attempts=attempt)
            except asyncio.TimeoutError:
                last_error = f"timeout_after_{timeout}s"
                self.observer.emit(task_id, "step_timeout", step_id=step_id, tool=tool, attempt=attempt, timeout_seconds=timeout)
            except Exception as exc:  # tool failures are data, not server crashes
                last_error = str(exc)
                self.observer.emit(task_id, "step_failed", step_id=step_id, tool=tool, attempt=attempt, error=last_error)

            if attempt < max_attempts:
                self.observer.emit(task_id, "step_retrying", step_id=step_id, tool=tool, attempt=attempt, next_attempt=attempt + 1)

        duration = int((perf_counter() - total_start) * 1000)
        return ExecutionResult("failed", error=last_error, duration_ms=duration, started_at=started_all, finished_at=self.now_fn(), attempts=max_attempts)

    async def execute_plan(self, task: dict[str, Any], order: list[str], approved_tools: set[str] | None = None) -> None:
        approved_tools = approved_tools or set()
        steps = {step["id"]: step for step in task["steps"]}
        self.reset(task["id"])
        self.observer.emit(task["id"], "execution_started", step_count=len(order))

        for step_id in order:
            if self.is_cancelled(task["id"]):
                task["status"] = "cancelled"
                self.observer.emit(task["id"], "execution_cancelled")
                return
            step = steps[step_id]
            step["status"] = "running"
            result = await self.execute_step(task, step, step["tool"] in approved_tools)
            step["attempts"] = result.attempts
            step["duration_ms"] = result.duration_ms
            step["started_at"] = result.started_at
            step["finished_at"] = result.finished_at
            if result.output is not None:
                step["output"] = result.output
            if result.error:
                step["error"] = result.error
            step["status"] = result.status
            if result.status != "completed":
                task["status"] = "cancelled" if result.status == "cancelled" else "failed"
                self.observer.emit(task["id"], "execution_stopped", status=task["status"], step_id=step_id)
                return

        task["status"] = "completed"
        self.observer.emit(task["id"], "execution_completed")

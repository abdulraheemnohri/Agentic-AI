from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Awaitable, Callable


@dataclass
class HealthState:
    healthy: bool = True
    checks: int = 0
    failures: int = 0
    last_check: str | None = None
    last_error: str | None = None


class System1HealthSupervisor:
    """System 1-owned health loop. It observes; it never delegates authority to System 2."""
    def __init__(self, interval: float = 5.0):
        self.interval = max(1.0, interval)
        self.state = HealthState()
        self._task: asyncio.Task | None = None
        self._check: Callable[[], Any] | None = None

    def bind(self, check: Callable[[], Any]) -> None:
        self._check = check

    async def start(self) -> None:
        if self._task and not self._task.done(): return
        self._task = asyncio.create_task(self._loop(), name="system1-health")

    async def _loop(self) -> None:
        while True:
            try:
                result = self._check() if self._check else True
                if asyncio.iscoroutine(result): result = await result
                self.state.healthy = bool(result)
                self.state.last_error = None if result else "system1_check_failed"
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                self.state.healthy = False
                self.state.failures += 1
                self.state.last_error = str(exc)
            self.state.checks += 1
            self.state.last_check = datetime.now(timezone.utc).isoformat()
            await asyncio.sleep(self.interval)

    async def shutdown(self) -> None:
        if self._task:
            self._task.cancel()
            try: await self._task
            except asyncio.CancelledError: pass
            self._task = None

    def snapshot(self) -> dict[str, Any]:
        return {"healthy": self.state.healthy, "checks": self.state.checks, "failures": self.state.failures, "last_check": self.state.last_check, "last_error": self.state.last_error, "authority": "system1"}

from __future__ import annotations

import asyncio
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Awaitable, Callable


@dataclass
class System1State:
    running: bool = False
    cycles: int = 0
    last_cycle_at: str | None = None
    last_error: str | None = None


class System1AutomaticBackend:
    """Always-on authority supervisor.

    System 1 owns policy, health checks and authorization. It never delegates
    authority to System 2 and can continue with the built-in guard when remote
    providers are unavailable.
    """

    def __init__(self, cycle_seconds: float = 5.0):
        self.cycle_seconds = max(1.0, cycle_seconds)
        self.state = System1State()
        self._task: asyncio.Task | None = None
        self._reviewer: Callable[[], Awaitable[dict[str, Any]]] | None = None

    def bind_reviewer(self, reviewer: Callable[[], Awaitable[dict[str, Any]]]) -> None:
        self._reviewer = reviewer

    def status(self) -> dict[str, Any]:
        return {
            "backend": "system1",
            "role": "authoritative_control_plane",
            "always_on": True,
            "running": self.state.running,
            "cycles": self.state.cycles,
            "last_cycle_at": self.state.last_cycle_at,
            "last_error": self.state.last_error,
            "cycle_seconds": self.cycle_seconds,
            "remote_fallback": "builtin_system1_guard",
            "system2_authority": False,
        }

    async def _cycle(self) -> None:
        self.state.cycles += 1
        self.state.last_cycle_at = datetime.now(timezone.utc).isoformat()
        self.state.last_error = None
        if self._reviewer:
            try:
                await self._reviewer()
            except Exception as exc:
                self.state.last_error = str(exc)

    async def _loop(self) -> None:
        self.state.running = True
        try:
            while True:
                await self._cycle()
                await asyncio.sleep(self.cycle_seconds)
        except asyncio.CancelledError:
            self.state.running = False
            raise

    def start(self) -> None:
        if self._task and not self._task.done():
            return
        self._task = asyncio.create_task(self._loop())

    def stop(self) -> None:
        # Public stop is intentionally disabled: System 1 must remain automatic.
        raise RuntimeError("system1_always_on:manual_stop_not_allowed")

    async def shutdown(self) -> None:
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        self.state.running = False

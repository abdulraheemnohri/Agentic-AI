from __future__ import annotations

import asyncio
import json
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Awaitable, Callable


@dataclass
class RuntimeConfig:
    max_concurrency: int = 2
    queue_limit: int = 20
    poll_interval_ms: int = 500


class ExecutionRuntime:
    """Small local execution supervisor for async AgentKernel jobs."""

    def __init__(self, root: Path | None = None) -> None:
        base = root or Path(__file__).resolve().parents[1]
        self.data_dir = base / "data"
        self.config_path = self.data_dir / "runtime_config.json"
        self.config = self._load_config()
        self.started_at = time.time()
        self._semaphore = asyncio.Semaphore(self.config.max_concurrency)
        self._tasks: dict[str, asyncio.Task[Any]] = {}
        self._queued = 0
        self._accepted = 0
        self._completed = 0
        self._failed = 0
        self._cancelled = 0

    def _load_config(self) -> RuntimeConfig:
        try:
            raw = json.loads(self.config_path.read_text(encoding="utf-8"))
            cfg = RuntimeConfig(**raw)
        except (FileNotFoundError, OSError, ValueError, TypeError):
            cfg = RuntimeConfig()
        cfg.max_concurrency = max(1, min(16, int(cfg.max_concurrency)))
        cfg.queue_limit = max(1, min(500, int(cfg.queue_limit)))
        cfg.poll_interval_ms = max(100, min(5000, int(cfg.poll_interval_ms)))
        return cfg

    def save_config(self, **changes: Any) -> RuntimeConfig:
        values = asdict(self.config)
        values.update(changes)
        cfg = RuntimeConfig(**values)
        cfg.max_concurrency = max(1, min(16, int(cfg.max_concurrency)))
        cfg.queue_limit = max(1, min(500, int(cfg.queue_limit)))
        cfg.poll_interval_ms = max(100, min(5000, int(cfg.poll_interval_ms)))
        self.config = cfg
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.config_path.write_text(json.dumps(asdict(cfg), indent=2), encoding="utf-8")
        # Replacing the semaphore only affects future jobs; running jobs keep their slot.
        self._semaphore = asyncio.Semaphore(cfg.max_concurrency)
        return cfg

    async def submit(self, job_id: str, work: Callable[[], Awaitable[Any]]) -> asyncio.Task[Any]:
        if job_id in self._tasks:
            raise ValueError("runtime_duplicate_job")
        if len(self._tasks) >= self.config.max_concurrency + self.config.queue_limit:
            raise RuntimeError("runtime_queue_full")
        self._accepted += 1
        self._queued += 1

        async def runner() -> Any:
            self._queued -= 1
            async with self._semaphore:
                try:
                    result = await work()
                    self._completed += 1
                    return result
                except asyncio.CancelledError:
                    self._cancelled += 1
                    raise
                except Exception:
                    self._failed += 1
                    raise
                finally:
                    self._tasks.pop(job_id, None)

        task = asyncio.create_task(runner(), name=f"agent-runtime:{job_id}")
        self._tasks[job_id] = task
        return task

    def cancel(self, job_id: str) -> bool:
        task = self._tasks.get(job_id)
        if not task or task.done():
            return False
        task.cancel()
        return True

    def status(self) -> dict[str, Any]:
        return {
            "runtime": "local_execution_runtime",
            "version": "3.0.0",
            "running": True,
            "uptime_seconds": round(time.time() - self.started_at, 3),
            "active_jobs": len(self._tasks) - self._queued,
            "queued_jobs": self._queued,
            "capacity": self.config.max_concurrency,
            "queue_limit": self.config.queue_limit,
            "accepted": self._accepted,
            "completed": self._completed,
            "failed": self._failed,
            "cancelled": self._cancelled,
            "config": asdict(self.config),
        }


runtime = ExecutionRuntime()

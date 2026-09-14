from __future__ import annotations

import asyncio
import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass
class RecoveryJob:
    run_id: str
    task_id: str
    status: str
    phase: str
    attempts: int = 0
    error: str | None = None
    updated_at: str = ""


class RecoveryManager:
    """Crash-safe bookkeeping for async runs and security/audit events."""

    def __init__(self, db_path: str | Path):
        self.db_path = str(db_path)
        self._lock = asyncio.Lock()
        self._ensure_schema()

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _ensure_schema(self) -> None:
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as c:
            c.executescript("""
            CREATE TABLE IF NOT EXISTS runtime_jobs (
              run_id TEXT PRIMARY KEY, task_id TEXT NOT NULL, status TEXT NOT NULL,
              phase TEXT NOT NULL, attempts INTEGER NOT NULL DEFAULT 0,
              error TEXT, updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS audit_events (
              id INTEGER PRIMARY KEY AUTOINCREMENT, event_type TEXT NOT NULL,
              run_id TEXT, task_id TEXT, actor TEXT NOT NULL,
              details TEXT NOT NULL, created_at TEXT NOT NULL
            );
            """)

    async def register(self, run_id: str, task_id: str, status: str = "queued", phase: str = "queued") -> None:
        async with self._lock:
            with self._connect() as c:
                c.execute("INSERT OR REPLACE INTO runtime_jobs VALUES (?,?,?,?,?,?,?)", (run_id, task_id, status, phase, 0, None, self._now()))

    async def update(self, run_id: str, status: str, phase: str, error: str | None = None) -> None:
        async with self._lock:
            with self._connect() as c:
                c.execute("UPDATE runtime_jobs SET status=?,phase=?,error=?,updated_at=? WHERE run_id=?", (status, phase, error, self._now(), run_id))

    def recoverable(self) -> list[dict[str, Any]]:
        with self._connect() as c:
            rows = c.execute("SELECT * FROM runtime_jobs WHERE status IN ('queued','running','observing','verifying','evaluating','retrying','replanning') ORDER BY updated_at").fetchall()
            return [dict(r) for r in rows]

    async def audit(self, event_type: str, actor: str, run_id: str | None = None, task_id: str | None = None, **details: Any) -> None:
        async with self._lock:
            with self._connect() as c:
                c.execute("INSERT INTO audit_events(event_type,run_id,task_id,actor,details,created_at) VALUES (?,?,?,?,?,?)", (event_type, run_id, task_id, actor, json.dumps(details, default=str), self._now()))

    def audit_list(self, limit: int = 200) -> list[dict[str, Any]]:
        with self._connect() as c:
            rows = c.execute("SELECT * FROM audit_events ORDER BY id DESC LIMIT ?", (max(1, min(limit, 1000)),)).fetchall()
            result = []
            for row in rows:
                item = dict(row)
                try: item["details"] = json.loads(item["details"])
                except Exception: pass
                result.append(item)
            return result

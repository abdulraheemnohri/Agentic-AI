from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any


class SQLiteStore:
    def __init__(self, path: str | Path = "data/agentic.db") -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.initialize()

    def connect(self):
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        return conn

    def initialize(self) -> None:
        with self.connect() as db:
            db.executescript(
                """
                CREATE TABLE IF NOT EXISTS tasks (
                    id TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    status TEXT NOT NULL,
                    goal TEXT NOT NULL,
                    autonomy INTEGER NOT NULL,
                    payload TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS evaluations (
                    id TEXT PRIMARY KEY,
                    task_id TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    FOREIGN KEY(task_id) REFERENCES tasks(id)
                );
                CREATE TABLE IF NOT EXISTS traces (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    payload TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS golden_cases (
                    case_id TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL,
                    payload TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS regression_runs (
                    run_id TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL,
                    payload TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS memories (
                    memory_id TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL,
                    kind TEXT NOT NULL,
                    importance REAL NOT NULL,
                    content TEXT NOT NULL,
                    metadata TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_evaluations_task ON evaluations(task_id);
                CREATE INDEX IF NOT EXISTS idx_traces_task ON traces(task_id);
                CREATE INDEX IF NOT EXISTS idx_memories_kind ON memories(kind);
                """
            )

    def save_task(self, task: dict[str, Any]) -> None:
        with self.connect() as db:
            db.execute("INSERT OR REPLACE INTO tasks VALUES (?, ?, ?, ?, ?, ?, ?)", (task["id"], task["created_at"], task["updated_at"], task["status"], task["goal"], task["autonomy"], json.dumps(task)))

    def load_tasks(self) -> list[dict[str, Any]]:
        with self.connect() as db:
            return [json.loads(row["payload"]) for row in db.execute("SELECT payload FROM tasks ORDER BY created_at DESC")]

    def save_evaluation(self, task_id: str, evaluation: dict[str, Any], created_at: str) -> str:
        import uuid
        item_id = str(uuid.uuid4())
        with self.connect() as db:
            db.execute("INSERT INTO evaluations VALUES (?, ?, ?, ?)", (item_id, task_id, created_at, json.dumps(evaluation)))
        return item_id

    def list_evaluations(self, task_id: str) -> list[dict[str, Any]]:
        with self.connect() as db:
            return [json.loads(row["payload"]) for row in db.execute("SELECT payload FROM evaluations WHERE task_id=? ORDER BY created_at DESC", (task_id,))]

    def save_trace_events(self, task_id: str, events: list[dict[str, Any]]) -> None:
        with self.connect() as db:
            db.execute("DELETE FROM traces WHERE task_id=?", (task_id,))
            db.executemany("INSERT INTO traces(task_id, created_at, payload) VALUES (?, ?, ?)", [(task_id, event.get("at", ""), json.dumps(event)) for event in events])

    def load_trace_events(self, task_id: str) -> list[dict[str, Any]]:
        with self.connect() as db:
            return [json.loads(row["payload"]) for row in db.execute("SELECT payload FROM traces WHERE task_id=? ORDER BY id", (task_id,))]

    def save_memory(self, memory: dict[str, Any]) -> None:
        with self.connect() as db:
            db.execute("INSERT OR REPLACE INTO memories VALUES (?, ?, ?, ?, ?, ?)", (memory["memory_id"], memory["created_at"], memory["kind"], memory["importance"], memory["content"], json.dumps(memory.get("metadata", {}))))

    def search_memories(self, query: str = "", kind: str | None = None, limit: int = 20) -> list[dict[str, Any]]:
        pattern = f"%{query}%"
        sql = "SELECT * FROM memories WHERE content LIKE ?"
        params: list[Any] = [pattern]
        if kind:
            sql += " AND kind=?"
            params.append(kind)
        sql += " ORDER BY importance DESC, created_at DESC LIMIT ?"
        params.append(limit)
        with self.connect() as db:
            return [{"memory_id": r["memory_id"], "created_at": r["created_at"], "kind": r["kind"], "importance": r["importance"], "content": r["content"], "metadata": json.loads(r["metadata"])} for r in db.execute(sql, params)]


store = SQLiteStore()

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4
from typing import Any

from .storage import store

MEMORY_KINDS = ("working", "episodic", "semantic", "procedural", "failure", "evaluation", "skill")


def remember(content: str, kind: str = "episodic", importance: float = 0.5, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    if kind not in MEMORY_KINDS:
        raise ValueError("unknown_memory_kind")
    if not content.strip():
        raise ValueError("memory_content_required")
    memory = {"memory_id": str(uuid4()), "created_at": datetime.now(timezone.utc).isoformat(), "kind": kind, "importance": max(0.0, min(1.0, importance)), "content": content.strip(), "metadata": metadata or {}}
    store.save_memory(memory)
    return memory


def recall(query: str = "", kind: str | None = None, limit: int = 20) -> list[dict[str, Any]]:
    if kind is not None and kind not in MEMORY_KINDS:
        raise ValueError("unknown_memory_kind")
    return store.search_memories(query, kind, max(1, min(100, limit)))

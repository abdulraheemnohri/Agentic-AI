from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4
from typing import Any

from .storage import store

MEMORY_KINDS = ("working", "episodic", "semantic", "procedural", "failure", "evaluation", "skill")


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def _recency_score(created_at: str) -> float:
    try:
        created = datetime.fromisoformat(created_at)
        age_days = max(0.0, (datetime.now(timezone.utc) - created).total_seconds() / 86400)
        return 1.0 / (1.0 + age_days / 30.0)
    except (TypeError, ValueError):
        return 0.0


def remember(content: str, kind: str = "episodic", importance: float = 0.5, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    if kind not in MEMORY_KINDS:
        raise ValueError("unknown_memory_kind")
    if not content.strip():
        raise ValueError("memory_content_required")
    memory = {
        "memory_id": str(uuid4()),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "kind": kind,
        "importance": _clamp(importance),
        "content": content.strip(),
        "metadata": metadata or {},
    }
    store.save_memory(memory)
    return memory


def recall(query: str = "", kind: str | None = None, limit: int = 20) -> list[dict[str, Any]]:
    if kind is not None and kind not in MEMORY_KINDS:
        raise ValueError("unknown_memory_kind")
    items = store.search_memories("", kind, 500)
    tokens = [token.lower() for token in query.split() if token.strip()]
    ranked: list[tuple[float, dict[str, Any]]] = []
    for item in items:
        text = item["content"].lower()
        if tokens and not any(token in text for token in tokens):
            continue
        matched = sum(token in text for token in tokens) / max(1, len(tokens))
        score = 0.60 * matched + 0.25 * _clamp(item["importance"]) + 0.15 * _recency_score(item["created_at"])
        enriched = dict(item)
        enriched["relevance_score"] = round(score, 4)
        ranked.append((score, enriched))
    ranked.sort(key=lambda pair: pair[0], reverse=True)
    return [item for _, item in ranked[: max(1, min(100, limit))]]


def learn_from_task(task: dict[str, Any]) -> list[dict[str, Any]]:
    """Create durable memories from important task outcomes without storing raw secrets."""
    created: list[dict[str, Any]] = []
    status = task.get("status", "unknown")
    goal = str(task.get("goal", "")).strip()
    evaluation = task.get("evaluation") or {}
    if goal:
        kind = "episodic" if status == "completed" else "failure"
        importance = 0.75 if status == "completed" else 0.85
        created.append(remember(f"Task outcome: {status}. Goal: {goal}", kind, importance, {"task_id": task.get("id"), "status": status}))
    if evaluation:
        score = _clamp(float(evaluation.get("overall_score", 0.0)))
        created.append(remember(f"Evaluation outcome: {evaluation.get('overall_status', 'unknown')} with score {score:.3f}.", "evaluation", 0.65, {"task_id": task.get("id"), "score": score}))
    return created

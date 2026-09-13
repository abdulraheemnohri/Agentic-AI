from __future__ import annotations

ALLOWED_TRANSITIONS: dict[str, set[str]] = {
    "created": {"planned", "cancelled"},
    "planned": {"waiting_approval", "cancelled"},
    "waiting_approval": {"running", "cancelled", "replanning"},
    "running": {"observing", "verifying", "failed", "cancelled"},
    "observing": {"running", "verifying", "failed"},
    "verifying": {"evaluating", "retrying", "failed"},
    "evaluating": {"completed", "retrying", "replanning", "escalated", "failed"},
    "retrying": {"running", "failed", "replanning"},
    "replanning": {"planned", "waiting_approval", "failed", "escalated"},
    "completed": set(),
    "failed": {"retrying", "replanning", "escalated"},
    "escalated": set(),
    "cancelled": set(),
}


def can_transition(current: str, target: str) -> bool:
    return target in ALLOWED_TRANSITIONS.get(current, set())


def transition(task: dict, target: str) -> None:
    current = task.get("status", "created")
    if current == target:
        return
    if not can_transition(current, target):
        raise ValueError(f"invalid_transition:{current}->{target}")
    task["status"] = target

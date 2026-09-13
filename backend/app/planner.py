from __future__ import annotations

from collections import defaultdict, deque
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class PlanStep(BaseModel):
    id: str
    title: str = Field(min_length=1, max_length=300)
    tool: str = Field(min_length=1, max_length=100)
    status: str = "pending"
    risk: str = "SAFE"
    depends_on: list[str] = Field(default_factory=list)
    retry_count: int = Field(default=0, ge=0, le=10)
    timeout_seconds: int = Field(default=60, ge=1, le=3600)
    requires_approval: bool = False
    success_criteria: str = "Tool completes without error."
    verification_method: str = "output_presence"
    failure_strategy: str = "retry"


class Plan(BaseModel):
    version: int = 1
    goal: str
    steps: list[PlanStep]


def build_default_plan(goal: str) -> Plan:
    return Plan(
        goal=goal,
        steps=[
            PlanStep(id="step-1", title="Understand goal", tool="echo", status="ready"),
            PlanStep(id="step-2", title="Execute safe action", tool="clock", depends_on=["step-1"], status="pending"),
            PlanStep(id="step-3", title="Verify result", tool="echo", depends_on=["step-2"], status="pending"),
        ],
    )


def validate_plan(plan: Plan, known_tools: set[str]) -> None:
    ids = [step.id for step in plan.steps]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate_step_id")
    known_ids = set(ids)
    for step in plan.steps:
        if step.tool not in known_tools:
            raise ValueError(f"unknown_tool:{step.tool}")
        if step.id in step.depends_on:
            raise ValueError("self_dependency")
        if any(dep not in known_ids for dep in step.depends_on):
            raise ValueError(f"missing_dependency:{step.id}")
    topological_order(plan)


def topological_order(plan: Plan) -> list[str]:
    graph: dict[str, list[str]] = defaultdict(list)
    indegree = {step.id: 0 for step in plan.steps}
    for step in plan.steps:
        for dep in step.depends_on:
            graph[dep].append(step.id)
            indegree[step.id] += 1
    queue = deque(step_id for step_id, degree in indegree.items() if degree == 0)
    result: list[str] = []
    while queue:
        current = queue.popleft()
        result.append(current)
        for child in graph[current]:
            indegree[child] -= 1
            if indegree[child] == 0:
                queue.append(child)
    if len(result) != len(plan.steps):
        raise ValueError("dependency_cycle")
    return result


def normalize_plan(payload: dict[str, Any], known_tools: set[str]) -> Plan:
    plan = Plan.model_validate(payload)
    validate_plan(plan, known_tools)
    return plan


def clone_step(step: PlanStep) -> PlanStep:
    data = step.model_dump()
    data["id"] = f"step-{uuid4().hex[:8]}"
    data["status"] = "pending"
    return PlanStep.model_validate(data)

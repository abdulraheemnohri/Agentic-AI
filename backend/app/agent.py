from __future__ import annotations

from dataclasses import dataclass, field
from time import perf_counter
from typing import Any, Callable
from uuid import uuid4

from .evaluator import evaluate_task
from .executor import Executor
from .memory import learn_from_task, recall
from .model_adapter import ModelRequest, get_model
from .observer import Observer
from .planner import Plan, build_default_plan, topological_order
from .tool_registry import authorization, list_tools
from .verifier import verify_task

PHASES = ("understanding", "memory_retrieval", "reasoning", "planning", "dry_run", "permission", "executing", "observing", "verifying", "evaluating", "recovering", "learning", "completed", "failed", "escalated", "cancelled")

@dataclass
class BrainDecision:
    action: str
    reason: str
    confidence: float
    plan_version: int
    memory_ids: list[str] = field(default_factory=list)
    model_id: str = ""
    suggested_tools: list[str] = field(default_factory=list)

@dataclass
class AgentRun:
    run_id: str
    task_id: str
    goal: str
    status: str = "created"
    phase: str = "understanding"
    iteration: int = 0
    max_iterations: int = 5
    max_retries: int = 2
    confidence_threshold: float = 0.70
    started_at: str = ""
    finished_at: str | None = None
    memory_context: list[dict[str, Any]] = field(default_factory=list)
    decisions: list[dict[str, Any]] = field(default_factory=list)
    stream: list[dict[str, Any]] = field(default_factory=list)
    error: str | None = None
    result: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return self.__dict__.copy()

class LocalBrain:
    """System 2 adapter. It proposes structured decisions but never executes tools."""
    async def reason(self, goal: str, memories: list[dict[str, Any]], plan: Plan) -> BrainDecision:
        response = await get_model().generate(ModelRequest(goal=goal, memories=memories, available_tools=list_tools(), constraints={"system1_authority": True, "plan_version": plan.version}))
        return BrainDecision(response.action, response.reason, response.confidence, plan.version, [m["memory_id"] for m in memories], response.model_id, response.suggested_tools)

class DeterministicBrain(LocalBrain):
    pass

class AgentKernel:
    """System 1 orchestration around a pluggable local System 2 brain."""
    def __init__(self, executor: Executor, observer: Observer, now_fn: Callable[[], str], emit: Callable[..., None] | None = None):
        self.executor, self.observer, self.now_fn = executor, observer, now_fn
        self.emit = emit or observer.emit
        self.brain = LocalBrain()
        self._cancelled: set[str] = set()

    def cancel(self, run_id: str) -> None: self._cancelled.add(run_id)
    def is_cancelled(self, run_id: str) -> bool: return run_id in self._cancelled
    def _stream(self, run: AgentRun, event: str, **data: Any) -> None:
        run.stream.append({"sequence": len(run.stream) + 1, "event": event, "at": self.now_fn(), **data})

    async def run(self, task: dict[str, Any], run: AgentRun, persist: Callable[[AgentRun], None]) -> AgentRun:
        started = perf_counter(); run.status, run.phase = "running", "understanding"; persist(run)
        self.emit(task["id"], "agent_run_started", run_id=run.run_id, goal=run.goal)
        try:
            while run.iteration < run.max_iterations:
                run.iteration += 1
                if self.is_cancelled(run.run_id):
                    run.status, run.phase, task["status"] = "cancelled", "cancelled", "cancelled"; break
                run.phase = "memory_retrieval"; run.memory_context = recall(run.goal, limit=8); self._stream(run, "memory_retrieved", count=len(run.memory_context)); persist(run)
                run.phase = "planning"; plan = build_default_plan(task["goal"]); plan.version = task.get("plan_version", 1); task["steps"] = [s.model_dump() for s in plan.steps]; task["plan_version"] = plan.version
                run.phase = "reasoning"; decision = await self.brain.reason(task["goal"], run.memory_context, plan)
                run.decisions.append({"iteration": run.iteration, "action": decision.action, "reason": decision.reason, "confidence": decision.confidence, "plan_version": decision.plan_version, "memory_ids": decision.memory_ids, "model_id": decision.model_id, "suggested_tools": decision.suggested_tools})
                self._stream(run, "brain_decision", model_id=decision.model_id, action=decision.action, confidence=decision.confidence)
                self.emit(task["id"], "agent_reasoning_decision", run_id=run.run_id, iteration=run.iteration, action=decision.action, confidence=decision.confidence, model_id=decision.model_id)
                run.phase = "dry_run"; order = topological_order(plan); permissions = []
                for step in plan.steps:
                    allowed, reason = authorization(step.tool, task["autonomy"], False); permissions.append({"step_id": step.id, "tool": step.tool, "allowed": allowed, "reason": reason})
                self._stream(run, "dry_run", execution_order=order, permissions=permissions); self.emit(task["id"], "agent_dry_run_completed", run_id=run.run_id, execution_order=order, permissions=permissions)
                if not all(p["allowed"] for p in permissions):
                    run.status, run.phase, run.error, task["status"] = "escalated", "escalated", "system1_permission_denied", "escalated"; break
                run.phase, task["status"] = "executing", "running"; await self.executor.execute_plan(task, order)
                run.phase = "observing"; self._stream(run, "observed", status=task["status"])
                run.phase = "verifying"; task["verification"] = verify_task(task); self._stream(run, "verified", passed=task["verification"]["passed"])
                run.phase = "evaluating"; task["evaluation"] = evaluate_task(task); self._stream(run, "evaluated", status=task["evaluation"]["overall_status"], score=task["evaluation"]["overall_score"])
                if task["status"] == "completed" and task["verification"]["passed"] and task["evaluation"]["overall_status"] == "passed" and decision.confidence >= run.confidence_threshold:
                    run.phase, run.status = "learning", "running"; learn_from_task(task); run.phase, run.status = "completed", "completed"; run.result = "Agent loop completed with local brain proposal and System 1 verification."; task["result"] = run.result; break
                run.phase = "recovering"
                if run.iteration >= run.max_iterations:
                    run.status, run.phase, run.error, task["status"] = "escalated", "escalated", "agent_max_iterations_reached", "escalated"; break
                for step in task["steps"]:
                    if step.get("status") != "completed": step["status"] = "pending"; step.pop("error", None); step.pop("output", None)
                self._stream(run, "recovery", iteration=run.iteration); persist(run)
            if run.status == "running": run.status, run.phase, run.error, task["status"] = "escalated", "escalated", "agent_loop_terminated_without_success", "escalated"
        except Exception as exc:
            run.status, run.phase, run.error, task["status"] = "failed", "failed", str(exc), "failed"
        finally:
            run.finished_at = self.now_fn(); persist(run); self.emit(task["id"], "agent_run_finished", run_id=run.run_id, status=run.status, duration_ms=int((perf_counter() - started) * 1000))
        return run

def new_run(task: dict[str, Any], now_fn: Callable[[], str], max_iterations: int = 5, max_retries: int = 2, confidence_threshold: float = 0.70) -> AgentRun:
    return AgentRun(str(uuid4()), task["id"], task["goal"], max_iterations=max(1, min(20, max_iterations)), max_retries=max(0, min(10, max_retries)), confidence_threshold=max(0.0, min(1.0, confidence_threshold)), started_at=now_fn())

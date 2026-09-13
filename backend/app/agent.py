from __future__ import annotations

from dataclasses import dataclass, field
from time import perf_counter
from typing import Any, Awaitable, Callable
from uuid import uuid4

from .evaluator import evaluate_task
from .executor import Executor
from .memory import learn_from_task, recall
from .observer import Observer
from .planner import Plan, build_default_plan, topological_order
from .verifier import verify_task
from .tool_registry import authorization


PHASES = (
    "understanding", "memory_retrieval", "reasoning", "planning", "dry_run",
    "permission", "executing", "observing", "verifying", "evaluating",
    "recovering", "learning", "completed", "failed", "escalated", "cancelled",
)


@dataclass
class BrainDecision:
    action: str
    reason: str
    confidence: float
    plan_version: int
    memory_ids: list[str] = field(default_factory=list)


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
    error: str | None = None
    result: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id, "task_id": self.task_id, "goal": self.goal,
            "status": self.status, "phase": self.phase, "iteration": self.iteration,
            "max_iterations": self.max_iterations, "max_retries": self.max_retries,
            "confidence_threshold": self.confidence_threshold,
            "started_at": self.started_at, "finished_at": self.finished_at,
            "memory_context": self.memory_context, "decisions": self.decisions,
            "error": self.error, "result": self.result,
        }


class DeterministicBrain:
    """System 2 proposal layer. It can propose; System 1 still authorizes every action."""

    def reason(self, goal: str, memory_context: list[dict[str, Any]], plan: Plan) -> BrainDecision:
        memory_ids = [m["memory_id"] for m in memory_context]
        confidence = 0.90 if plan.steps else 0.20
        if any(m.get("kind") == "failure" for m in memory_context):
            confidence = max(0.70, confidence - 0.10)
        return BrainDecision(
            action="execute_guarded_plan",
            reason="Selected the validated local plan; prior memory is advisory only and cannot bypass System 1 controls.",
            confidence=confidence,
            plan_version=plan.version,
            memory_ids=memory_ids,
        )


class AgentKernel:
    """System 1 orchestration around a pluggable System 2 brain."""

    def __init__(self, executor: Executor, observer: Observer, now_fn: Callable[[], str], emit: Callable[..., None] | None = None):
        self.executor = executor
        self.observer = observer
        self.now_fn = now_fn
        self.emit = emit or observer.emit
        self.brain = DeterministicBrain()
        self._cancelled: set[str] = set()

    def cancel(self, run_id: str) -> None:
        self._cancelled.add(run_id)

    def is_cancelled(self, run_id: str) -> bool:
        return run_id in self._cancelled

    async def run(self, task: dict[str, Any], run: AgentRun, persist: Callable[[AgentRun], None]) -> AgentRun:
        started = perf_counter()
        run.status = "running"
        run.phase = "understanding"
        persist(run)
        self.emit(task["id"], "agent_run_started", run_id=run.run_id, goal=run.goal)

        try:
            while run.iteration < run.max_iterations:
                run.iteration += 1
                if self.is_cancelled(run.run_id):
                    run.status, run.phase = "cancelled", "cancelled"
                    task["status"] = "cancelled"
                    break

                run.phase = "memory_retrieval"
                run.memory_context = recall(run.goal, limit=8)
                persist(run)
                self.emit(task["id"], "agent_memory_retrieved", run_id=run.run_id, count=len(run.memory_context))

                run.phase = "planning"
                plan = build_default_plan(task["goal"])
                plan.version = task.get("plan_version", 1)
                task["steps"] = [s.model_dump() for s in plan.steps]
                task["plan_version"] = plan.version
                persist(run)

                run.phase = "reasoning"
                decision = self.brain.reason(task["goal"], run.memory_context, plan)
                run.decisions.append({"iteration": run.iteration, "action": decision.action, "reason": decision.reason, "confidence": decision.confidence, "plan_version": decision.plan_version, "memory_ids": decision.memory_ids})
                self.emit(task["id"], "agent_reasoning_decision", run_id=run.run_id, iteration=run.iteration, action=decision.action, confidence=decision.confidence, reason=decision.reason)

                run.phase = "dry_run"
                order = topological_order(plan)
                permission_results = []
                blocked = False
                for step in plan.steps:
                    allowed, reason = authorization(step.tool, task["autonomy"], False)
                    permission_results.append({"step_id": step.id, "tool": step.tool, "allowed": allowed, "reason": reason})
                    if not allowed:
                        blocked = True
                self.emit(task["id"], "agent_dry_run_completed", run_id=run.run_id, execution_order=order, permissions=permission_results)

                run.phase = "permission"
                if blocked:
                    run.status, run.phase = "escalated", "escalated"
                    run.error = "system1_permission_denied"
                    task["status"] = "escalated"
                    break

                run.phase = "executing"
                task["status"] = "running"
                await self.executor.execute_plan(task, order)
                run.phase = "observing"
                self.emit(task["id"], "agent_observation_complete", run_id=run.run_id, status=task["status"])

                run.phase = "verifying"
                verification = verify_task(task)
                task["verification"] = verification
                self.emit(task["id"], "agent_verification_complete", run_id=run.run_id, passed=verification["passed"])

                run.phase = "evaluating"
                evaluation = evaluate_task(task)
                task["evaluation"] = evaluation
                self.emit(task["id"], "agent_evaluation_complete", run_id=run.run_id, status=evaluation["overall_status"], score=evaluation["overall_score"])

                if task["status"] == "completed" and verification["passed"] and evaluation["overall_status"] == "passed" and decision.confidence >= run.confidence_threshold:
                    run.phase, run.status = "learning", "running"
                    learn_from_task(task)
                    run.phase, run.status = "completed", "completed"
                    run.result = "Agent loop completed: plan executed, observed, verified, evaluated and learned."
                    task["result"] = run.result
                    break

                run.phase = "recovering"
                if run.iteration >= run.max_iterations:
                    run.status, run.phase = "escalated", "escalated"
                    run.error = "agent_max_iterations_reached"
                    task["status"] = "escalated"
                    break
                if task["status"] in {"failed", "cancelled"}:
                    for step in task["steps"]:
                        if step.get("status") != "completed":
                            step["status"] = "pending"
                            step.pop("error", None)
                            step.pop("output", None)
                    self.emit(task["id"], "agent_recovery_retry", run_id=run.run_id, iteration=run.iteration)
                else:
                    self.emit(task["id"], "agent_recovery_replan", run_id=run.run_id, iteration=run.iteration)

                persist(run)

            if run.status == "running":
                run.status, run.phase = "escalated", "escalated"
                run.error = "agent_loop_terminated_without_success"
                task["status"] = "escalated"
        except Exception as exc:
            run.status, run.phase = "failed", "failed"
            run.error = str(exc)
            task["status"] = "failed"
        finally:
            run.finished_at = self.now_fn()
            persist(run)
            self.emit(task["id"], "agent_run_finished", run_id=run.run_id, status=run.status, duration_ms=int((perf_counter() - started) * 1000))
        return run


def new_run(task: dict[str, Any], now_fn: Callable[[], str], max_iterations: int = 5, max_retries: int = 2, confidence_threshold: float = 0.70) -> AgentRun:
    return AgentRun(run_id=str(uuid4()), task_id=task["id"], goal=task["goal"], max_iterations=max(1, min(20, max_iterations)), max_retries=max(0, min(10, max_retries)), confidence_threshold=max(0.0, min(1.0, confidence_threshold)), started_at=now_fn())

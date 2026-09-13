from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from .evaluator import evaluate_task
from .executor import Executor
from .observer import observer
from .planner import Plan, build_default_plan, normalize_plan, topological_order
from .regression import golden_dataset, regression_engine
from .tool_registry import authorization, list_tools, set_policy
from .verifier import verify_task

app = FastAPI(title="Agentic-AI", version="1.7.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
tasks: dict[str, dict[str, Any]] = {}


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


executor = Executor(observer, now)


class TaskCreate(BaseModel):
    goal: str = Field(min_length=1, max_length=10000)
    autonomy: int = Field(default=1, ge=0, le=5)


class Approval(BaseModel):
    approved: bool


class PlanUpdate(BaseModel):
    plan: Plan


class ToolPolicyUpdate(BaseModel):
    policy: str | None = None
    enabled: bool | None = None
    risk: str | None = None


class HumanReview(BaseModel):
    score: float = Field(ge=0, le=1)
    label: str = "reviewed"
    notes: str = ""


class GoldenCaseCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    goal: str = Field(min_length=1, max_length=10000)
    expected_checks: dict[str, bool] = {}
    expected_status: str = "passed"
    tags: list[str] = []


def run_evaluation(task: dict[str, Any]) -> dict[str, Any]:
    result = evaluate_task(task, review=task.get("human_review"))
    task["evaluation"] = result
    observer.emit(task["id"], "evaluation_completed", status=result["overall_status"], score=result["overall_score"], confidence=result["confidence"])
    return result


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "agentic-ai", "version": app.version}


@app.get("/api/tools")
def tools():
    return {tool["name"]: tool for tool in list_tools()}


@app.get("/api/tools/{tool_name}")
def tool_detail(tool_name: str):
    tools_map = {tool["name"]: tool for tool in list_tools()}
    if tool_name not in tools_map:
        raise HTTPException(404, "tool_not_found")
    return tools_map[tool_name]


@app.put("/api/tools/{tool_name}/policy")
def update_tool_policy(tool_name: str, request: ToolPolicyUpdate):
    try:
        return set_policy(tool_name, request.policy, request.enabled, request.risk).as_dict()
    except KeyError as exc:
        raise HTTPException(404, "tool_not_found") from exc
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc


@app.post("/api/tasks")
def create_task(request: TaskCreate):
    task_id = str(uuid4())
    plan = build_default_plan(request.goal)
    task = {"id": task_id, "goal": request.goal, "autonomy": request.autonomy, "status": "planned", "created_at": now(), "updated_at": now(), "plan_version": plan.version, "steps": [s.model_dump() for s in plan.steps], "events": [{"type": "task_created", "at": now()}], "verification": None, "evaluation": None, "human_review": None, "result": None}
    tasks[task_id] = task
    observer.emit(task_id, "task_created", goal=request.goal, autonomy=request.autonomy)
    return task


@app.get("/api/tasks")
def list_tasks():
    return sorted(tasks.values(), key=lambda t: t["created_at"], reverse=True)


@app.get("/api/tasks/{task_id}")
def get_task(task_id: str):
    if task_id not in tasks:
        raise HTTPException(404, "task_not_found")
    return tasks[task_id]


@app.get("/api/tasks/{task_id}/plan")
def get_plan(task_id: str):
    task = tasks.get(task_id)
    if not task:
        raise HTTPException(404, "task_not_found")
    plan = Plan.model_validate({"version": task["plan_version"], "goal": task["goal"], "steps": task["steps"]})
    return {"version": plan.version, "goal": plan.goal, "steps": plan.steps, "order": topological_order(plan)}


@app.put("/api/tasks/{task_id}/plan")
def update_plan(task_id: str, request: PlanUpdate):
    task = tasks.get(task_id)
    if not task:
        raise HTTPException(404, "task_not_found")
    if task["status"] in {"running", "completed", "cancelled"}:
        raise HTTPException(409, "plan_locked")
    try:
        plan = normalize_plan(request.plan.model_dump(), {tool["name"] for tool in list_tools()})
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    plan.version = task["plan_version"] + 1
    task.update({"plan_version": plan.version, "goal": plan.goal, "steps": [s.model_dump() for s in plan.steps], "updated_at": now()})
    observer.emit(task_id, "plan_updated", version=plan.version)
    return task


@app.post("/api/tasks/{task_id}/dry-run")
def dry_run(task_id: str):
    task = tasks.get(task_id)
    if not task:
        raise HTTPException(404, "task_not_found")
    plan = Plan.model_validate({"version": task["plan_version"], "goal": task["goal"], "steps": task["steps"]})
    permissions = [{"step_id": s.id, "tool": s.tool, "allowed": authorization(s.tool, task["autonomy"])[0], "reason": authorization(s.tool, task["autonomy"])[1]} for s in plan.steps]
    return {"valid": True, "version": plan.version, "execution_order": topological_order(plan), "step_count": len(plan.steps), "permissions": permissions, "message": "Plan, dependencies and tool permissions validated; no tools were executed."}


@app.post("/api/tasks/{task_id}/replan")
def replan(task_id: str):
    task = tasks.get(task_id)
    if not task:
        raise HTTPException(404, "task_not_found")
    if task["status"] in {"running", "completed", "cancelled"}:
        raise HTTPException(409, "cannot_replan_current_state")
    plan = build_default_plan(task["goal"])
    plan.version = task["plan_version"] + 1
    task.update({"plan_version": plan.version, "steps": [s.model_dump() for s in plan.steps], "status": "planned", "updated_at": now()})
    observer.emit(task_id, "plan_rebuilt", version=plan.version)
    return task


@app.post("/api/tasks/{task_id}/approve")
async def approve_task(task_id: str, request: Approval):
    task = tasks.get(task_id)
    if not task:
        raise HTTPException(404, "task_not_found")
    if task["status"] != "planned":
        raise HTTPException(409, f"invalid_task_state:{task['status']}")
    if not request.approved:
        task["status"] = "cancelled"
        observer.emit(task_id, "plan_rejected")
        return task
    task["status"] = "running"
    observer.emit(task_id, "plan_approved", version=task["plan_version"])
    plan = Plan.model_validate({"version": task["plan_version"], "goal": task["goal"], "steps": task["steps"]})
    await executor.execute_plan(task, topological_order(plan))
    task["updated_at"] = now()
    task["verification"] = verify_task(task)
    if task["status"] == "completed" and task["verification"]["passed"]:
        task["result"] = "V1.7 execution completed and verified."
        observer.emit(task_id, "verification_passed", verification=task["verification"])
    else:
        task["status"] = "failed" if task["status"] == "completed" else task["status"]
        task["result"] = "Execution did not satisfy verification."
        observer.emit(task_id, "verification_failed", verification=task["verification"])
    run_evaluation(task)
    return task


@app.post("/api/tasks/{task_id}/cancel")
def cancel_task(task_id: str):
    task = tasks.get(task_id)
    if not task:
        raise HTTPException(404, "task_not_found")
    executor.cancel(task_id)
    if task["status"] in {"planned", "running"}:
        task["status"] = "cancelled"
    task["updated_at"] = now()
    return task


@app.get("/api/tasks/{task_id}/trace")
def task_trace(task_id: str):
    if task_id not in tasks:
        raise HTTPException(404, "task_not_found")
    return {"task_id": task_id, "events": observer.list(task_id)}


@app.get("/api/tasks/{task_id}/verification")
def task_verification(task_id: str):
    task = tasks.get(task_id)
    if not task:
        raise HTTPException(404, "task_not_found")
    return task.get("verification") or verify_task(task)


@app.post("/api/tasks/{task_id}/retry")
async def retry_task(task_id: str):
    task = tasks.get(task_id)
    if not task:
        raise HTTPException(404, "task_not_found")
    if task["status"] not in {"failed", "cancelled"}:
        raise HTTPException(409, f"cannot_retry_current_state:{task['status']}")
    for step in task["steps"]:
        if step["status"] != "completed":
            step["status"] = "pending"
            step.pop("error", None)
            step.pop("output", None)
    task["status"] = "running"
    observer.emit(task_id, "retry_started")
    plan = Plan.model_validate({"version": task["plan_version"], "goal": task["goal"], "steps": task["steps"]})
    await executor.execute_plan(task, topological_order(plan))
    task["verification"] = verify_task(task)
    if task["status"] == "completed" and not task["verification"]["passed"]:
        task["status"] = "failed"
    elif task["status"] == "completed":
        observer.emit(task_id, "verification_passed", verification=task["verification"])
    run_evaluation(task)
    task["updated_at"] = now()
    return task


@app.post("/api/tasks/{task_id}/verify")
def verify_task_endpoint(task_id: str):
    task = tasks.get(task_id)
    if not task:
        raise HTTPException(404, "task_not_found")
    result = verify_task(task)
    task["verification"] = result
    observer.emit(task_id, "verification_passed" if result["passed"] else "verification_failed", verification=result)
    return result


@app.get("/api/tasks/{task_id}/evaluation")
def get_evaluation(task_id: str):
    task = tasks.get(task_id)
    if not task:
        raise HTTPException(404, "task_not_found")
    return task.get("evaluation") or run_evaluation(task)


@app.post("/api/tasks/{task_id}/evaluate")
def evaluate_endpoint(task_id: str):
    task = tasks.get(task_id)
    if not task:
        raise HTTPException(404, "task_not_found")
    return run_evaluation(task)


@app.post("/api/tasks/{task_id}/human-review")
def human_review(task_id: str, review: HumanReview):
    task = tasks.get(task_id)
    if not task:
        raise HTTPException(404, "task_not_found")
    task["human_review"] = review.model_dump()
    observer.emit(task_id, "human_review_submitted", score=review.score, label=review.label)
    return run_evaluation(task)


@app.get("/api/golden")
def list_golden_cases():
    return {"count": len(golden_dataset.list()), "cases": golden_dataset.list()}


@app.post("/api/golden")
def add_golden_case(request: GoldenCaseCreate):
    if request.expected_status not in {"passed", "failed"}:
        raise HTTPException(422, "expected_status_must_be_passed_or_failed")
    case = golden_dataset.add(request.name, request.goal, request.expected_checks, request.expected_status, request.tags)
    return case.as_dict()


@app.delete("/api/golden/{case_id}")
def delete_golden_case(case_id: str):
    if not golden_dataset.remove(case_id):
        raise HTTPException(404, "golden_case_not_found")
    return {"deleted": True, "case_id": case_id}


@app.post("/api/regression/run")
def run_regression():
    result = regression_engine.run(evaluate_task)
    observer.emit("regression", "regression_completed", run_id=result.run_id, passed=result.passed, total=result.total)
    return result.as_dict()


@app.get("/api/regression/history")
def regression_history():
    return {"runs": regression_engine.list_history()}

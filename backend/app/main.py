from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from .executor import Executor
from .observer import observer
from .planner import Plan, build_default_plan, normalize_plan, topological_order
from .tool_registry import authorization, list_tools, set_policy

app = FastAPI(title="Agentic-AI", version="1.4.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

tasks: dict[str, dict[str, Any]] = {}


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def deterministic_evaluate(task: dict[str, Any]) -> dict[str, Any]:
    checks = {
        "task_has_goal": bool(task.get("goal", "").strip()),
        "plan_exists": bool(task.get("steps")),
        "all_steps_completed": all(s["status"] == "completed" for s in task.get("steps", [])),
        "verification_passed": task.get("verification", {}).get("passed", False),
    }
    return {"status": "passed" if all(checks.values()) else "failed", "score": round(sum(checks.values()) / len(checks), 3), "checks": checks}


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
    task = {
        "id": task_id,
        "goal": request.goal,
        "autonomy": request.autonomy,
        "status": "planned",
        "created_at": now(),
        "updated_at": now(),
        "plan_version": plan.version,
        "steps": [s.model_dump() for s in plan.steps],
        "events": [{"type": "task_created", "at": now()}],
        "verification": None,
        "evaluation": None,
        "result": None,
    }
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
    task["plan_version"] = plan.version
    task["goal"] = plan.goal
    task["steps"] = [s.model_dump() for s in plan.steps]
    task["updated_at"] = now()
    task["events"].append({"type": "plan_updated", "at": now(), "version": plan.version})
    observer.emit(task_id, "plan_updated", version=plan.version)
    return task


@app.post("/api/tasks/{task_id}/dry-run")
def dry_run(task_id: str):
    task = tasks.get(task_id)
    if not task:
        raise HTTPException(404, "task_not_found")
    plan = Plan.model_validate({"version": task["plan_version"], "goal": task["goal"], "steps": task["steps"]})
    order = topological_order(plan)
    permissions = []
    for step in plan.steps:
        allowed, reason = authorization(step.tool, task["autonomy"])
        permissions.append({"step_id": step.id, "tool": step.tool, "allowed": allowed, "reason": reason})
    return {"valid": True, "version": plan.version, "execution_order": order, "step_count": len(plan.steps), "permissions": permissions, "message": "Plan and tool permissions validated; no tools were executed."}


@app.post("/api/tasks/{task_id}/replan")
def replan(task_id: str):
    task = tasks.get(task_id)
    if not task:
        raise HTTPException(404, "task_not_found")
    if task["status"] in {"running", "completed", "cancelled"}:
        raise HTTPException(409, "cannot_replan_current_state")
    plan = build_default_plan(task["goal"])
    plan.version = task["plan_version"] + 1
    task["plan_version"] = plan.version
    task["steps"] = [s.model_dump() for s in plan.steps]
    task["status"] = "planned"
    task["updated_at"] = now()
    task["events"].append({"type": "plan_rebuilt", "at": now(), "version": plan.version})
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
        task["events"].append({"type": "plan_rejected", "at": now()})
        observer.emit(task_id, "plan_rejected")
        return task
    task["status"] = "running"
    task["events"].append({"type": "plan_approved", "at": now(), "version": task["plan_version"]})
    plan = Plan.model_validate({"version": task["plan_version"], "goal": task["goal"], "steps": task["steps"]})
    await executor.execute_plan(task, topological_order(plan))
    if task["status"] == "completed":
        task["verification"] = {"passed": True, "method": "deterministic_output_presence", "at": now()}
        task["result"] = "V1.4 execution completed and observed."
    elif task["status"] == "cancelled":
        task["result"] = "Execution cancelled."
    else:
        task["result"] = "Execution stopped after a step failure or permission block."
    task["updated_at"] = now()
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
    task["events"].append({"type": "task_cancel_requested", "at": now()})
    return task


@app.get("/api/tasks/{task_id}/trace")
def task_trace(task_id: str):
    if task_id not in tasks:
        raise HTTPException(404, "task_not_found")
    return {"task_id": task_id, "events": observer.list(task_id)}


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
    task["events"].append({"type": "retry_started", "at": now()})
    plan = Plan.model_validate({"version": task["plan_version"], "goal": task["goal"], "steps": task["steps"]})
    await executor.execute_plan(task, topological_order(plan))
    task["updated_at"] = now()
    return task


@app.post("/api/tasks/{task_id}/evaluate")
def evaluate_task(task_id: str):
    task = tasks.get(task_id)
    if not task:
        raise HTTPException(404, "task_not_found")
    deterministic = deterministic_evaluate(task)
    task["evaluation"] = {
        "deterministic": deterministic,
        "judge": {"status": "not_configured", "score": None},
        "human": {"status": "not_required", "score": None},
        "overall_status": deterministic["status"],
    }
    task["events"].append({"type": "evaluation_completed", "at": now(), "score": deterministic["score"]})
    observer.emit(task_id, "evaluation_completed", score=deterministic["score"])
    return task["evaluation"]

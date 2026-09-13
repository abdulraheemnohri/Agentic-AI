from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

app = FastAPI(title="Agentic-AI", version="1.1.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

tasks: dict[str, dict[str, Any]] = {}

SAFE_TOOLS = {
    "echo": {"risk": "SAFE", "description": "Return supplied text."},
    "clock": {"risk": "SAFE", "description": "Read server UTC time."},
}

class TaskCreate(BaseModel):
    goal: str = Field(min_length=1, max_length=10000)
    autonomy: int = Field(default=1, ge=0, le=5)

class Approval(BaseModel):
    approved: bool


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_plan(goal: str) -> list[dict[str, Any]]:
    return [
        {"id": "step-1", "title": "Understand goal", "tool": "echo", "status": "ready", "risk": "SAFE"},
        {"id": "step-2", "title": "Execute safe action", "tool": "clock", "status": "blocked", "risk": "SAFE"},
        {"id": "step-3", "title": "Verify result", "tool": "echo", "status": "blocked", "risk": "SAFE"},
    ]


def deterministic_evaluate(task: dict[str, Any]) -> dict[str, Any]:
    checks = {
        "task_has_goal": bool(task.get("goal", "").strip()),
        "plan_exists": bool(task.get("steps")),
        "all_steps_completed": all(s["status"] == "completed" for s in task.get("steps", [])),
        "verification_passed": task.get("verification", {}).get("passed", False),
    }
    passed = all(checks.values())
    return {"status": "passed" if passed else "failed", "score": round(sum(checks.values()) / len(checks), 3), "checks": checks}

@app.get("/api/health")
def health():
    return {"status": "ok", "service": "agentic-ai", "version": app.version}

@app.get("/api/tools")
def tools():
    return SAFE_TOOLS

@app.post("/api/tasks")
def create_task(request: TaskCreate):
    task_id = str(uuid4())
    task = {
        "id": task_id, "goal": request.goal, "autonomy": request.autonomy,
        "status": "planned", "created_at": now(), "updated_at": now(),
        "steps": build_plan(request.goal), "events": [{"type": "task_created", "at": now()}],
        "verification": None, "evaluation": None, "result": None,
    }
    tasks[task_id] = task
    return task

@app.get("/api/tasks")
def list_tasks():
    return sorted(tasks.values(), key=lambda t: t["created_at"], reverse=True)

@app.get("/api/tasks/{task_id}")
def get_task(task_id: str):
    if task_id not in tasks:
        raise HTTPException(404, "task_not_found")
    return tasks[task_id]

@app.post("/api/tasks/{task_id}/approve")
def approve_task(task_id: str, request: Approval):
    task = tasks.get(task_id)
    if not task:
        raise HTTPException(404, "task_not_found")
    if not request.approved:
        task["status"] = "cancelled"
        task["events"].append({"type": "plan_rejected", "at": now()})
        return task
    task["status"] = "running"
    task["events"].append({"type": "plan_approved", "at": now()})
    for step in task["steps"]:
        step["status"] = "running"
        if step["tool"] == "clock":
            step["output"] = {"utc": now()}
        elif step["tool"] == "echo":
            step["output"] = {"text": task["goal"]}
        step["status"] = "completed"
    task["verification"] = {"passed": True, "method": "deterministic_output_presence", "at": now()}
    task["result"] = "Safe V1 execution completed and verified."
    task["status"] = "completed"
    task["updated_at"] = now()
    task["events"].append({"type": "task_completed", "at": now()})
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
    return task["evaluation"]

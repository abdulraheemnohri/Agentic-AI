from fastapi import FastAPI
from pydantic import BaseModel, Field
from uuid import uuid4
from datetime import datetime, timezone

app = FastAPI(title="Agentic-AI", version="1.0.0")

tasks: dict[str, dict] = {}

class TaskCreate(BaseModel):
    goal: str = Field(min_length=1, max_length=10000)
    autonomy: int = Field(default=1, ge=0, le=5)

@app.get("/api/health")
def health():
    return {"status": "ok", "service": "agentic-ai", "version": app.version}

@app.post("/api/tasks")
def create_task(request: TaskCreate):
    task_id = str(uuid4())
    now = datetime.now(timezone.utc).isoformat()
    task = {
        "id": task_id,
        "goal": request.goal,
        "autonomy": request.autonomy,
        "status": "planned",
        "created_at": now,
        "steps": [],
        "evaluation": None,
    }
    tasks[task_id] = task
    return task

@app.get("/api/tasks")
def list_tasks():
    return list(tasks.values())

@app.get("/api/tasks/{task_id}")
def get_task(task_id: str):
    task = tasks.get(task_id)
    if not task:
        return {"error": "task_not_found"}
    return task

@app.post("/api/tasks/{task_id}/evaluate")
def evaluate_task(task_id: str):
    task = tasks.get(task_id)
    if not task:
        return {"error": "task_not_found"}
    task["evaluation"] = {
        "deterministic": {"status": "pending"},
        "judge": {"status": "pending"},
        "human": {"status": "not_required"},
    }
    return task["evaluation"]

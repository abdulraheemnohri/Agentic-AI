from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from .agent import AgentKernel, new_run
from .brain_routes import router as brain_router
from .evaluator import evaluate_task
from .executor import Executor
from .memory import MEMORY_KINDS, learn_from_task, recall, remember
from .observer import observer
from .planner import Plan, build_default_plan, normalize_plan, topological_order
from .regression import golden_dataset, regression_engine
from .storage import store
from .tool_registry import authorization, list_tools, set_policy
from .verifier import verify_task

app = FastAPI(title="Agentic-AI", version="2.5.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.include_router(brain_router)
tasks: dict[str, dict[str, Any]] = {task["id"]: task for task in store.load_tasks()}
agent_runs: dict[str, dict[str, Any]] = {run["run_id"]: run for run in store.load_agent_runs()}

def now() -> str:
    return datetime.now(timezone.utc).isoformat()

def persist(task: dict[str, Any]) -> None:
    task["updated_at"] = now(); store.save_task(task); store.save_trace_events(task["id"], observer.list(task["id"]))

def emit(task_id: str, event_type: str, **payload: Any) -> None:
    observer.emit(task_id, event_type, **payload)
    if task_id in tasks: persist(tasks[task_id])

executor = Executor(observer, now)
agent_kernel = AgentKernel(executor, observer, now, emit)

class TaskCreate(BaseModel):
    goal: str = Field(min_length=1, max_length=10000)
    autonomy: int = Field(default=1, ge=0, le=5)
class AgentRunCreate(BaseModel):
    goal: str = Field(min_length=1, max_length=10000)
    autonomy: int = Field(default=1, ge=0, le=5)
    max_iterations: int = Field(default=5, ge=1, le=50)
    max_retries: int = Field(default=2, ge=0, le=10)
    confidence_threshold: float = Field(default=0.7, ge=0, le=1)
class Approval(BaseModel): approved: bool
class HumanReview(BaseModel): approved: bool; score: float = Field(ge=0, le=1); confidence: float = Field(ge=0, le=1); notes: str = ""
class MemoryCreate(BaseModel): content: str = Field(min_length=1, max_length=20000); kind: str = "working"; importance: float = Field(default=.5, ge=0, le=1); tags: list[str] = Field(default_factory=list)
class GoldenCreate(BaseModel): name: str; goal: str; expected: dict[str, bool]
class ToolPolicy(BaseModel): tool: str; policy: str

@app.get("/health")
def health() -> dict[str, Any]:
    return {"status":"ok","version":"2.5.0","agent_kernel":"system1-authoritative-v2.5","system1_authoritative":True,"system2_local_only":True,"storage":"sqlite"}

@app.get("/api/tasks")
def list_tasks(status: str | None = Query(default=None)):
    values = list(tasks.values())
    if status: values = [task for task in values if task.get("status") == status]
    return sorted(values, key=lambda item: item.get("created_at", ""), reverse=True)

@app.post("/api/tasks")
def create_task(request: TaskCreate):
    task_id = str(uuid4()); task = {"id":task_id,"goal":request.goal,"autonomy":request.autonomy,"status":"created","created_at":now(),"updated_at":now(),"plan":build_default_plan(request.goal).model_dump(),"approval":None,"result":None}
    tasks[task_id] = task; persist(task); return task

@app.get("/api/tasks/{task_id}")
def get_task(task_id: str):
    if task_id not in tasks: raise HTTPException(404,"task_not_found")
    return tasks[task_id]

@app.get("/api/tasks/{task_id}/plan")
def get_plan(task_id: str):
    if task_id not in tasks: raise HTTPException(404,"task_not_found")
    return tasks[task_id]["plan"]

@app.put("/api/tasks/{task_id}/plan")
def update_plan(task_id: str, plan: Plan):
    if task_id not in tasks: raise HTTPException(404,"task_not_found")
    try: normalize_plan(plan); tasks[task_id]["plan"] = plan.model_dump(); persist(tasks[task_id]); return tasks[task_id]["plan"]
    except ValueError as exc: raise HTTPException(422,str(exc)) from exc

@app.post("/api/tasks/{task_id}/dry-run")
def dry_run(task_id: str):
    if task_id not in tasks: raise HTTPException(404,"task_not_found")
    plan = Plan.model_validate(tasks[task_id]["plan"]); order = topological_order(plan)
    return {"task_id":task_id,"mode":"dry_run","steps":[{"step_id":step.id,"tool":step.tool,"risk":step.risk,"depends_on":step.depends_on,"requires_approval":step.requires_approval} for step in order]}

@app.post("/api/tasks/{task_id}/approve")
async def approve(task_id: str, request: Approval):
    if task_id not in tasks: raise HTTPException(404,"task_not_found")
    task=tasks[task_id]; task["approval"]=request.approved
    if not request.approved: task["status"]="cancelled"; persist(task); return task
    result=await executor.execute(task); task["status"]=result.status; task["result"]=result.model_dump() if hasattr(result,"model_dump") else result; persist(task); return task

@app.post("/api/tasks/{task_id}/cancel")
async def cancel_task(task_id: str):
    if task_id not in tasks: raise HTTPException(404,"task_not_found")
    executor.cancel(task_id); tasks[task_id]["status"]="cancelled"; persist(tasks[task_id]); return tasks[task_id]

@app.post("/api/tasks/{task_id}/retry")
async def retry_task(task_id: str):
    if task_id not in tasks: raise HTTPException(404,"task_not_found")
    result=await executor.execute(tasks[task_id]); tasks[task_id]["status"]=result.status; tasks[task_id]["result"]=result.model_dump() if hasattr(result,"model_dump") else result; persist(tasks[task_id]); return tasks[task_id]

@app.get("/api/tasks/{task_id}/trace")
def task_trace(task_id: str):
    if task_id not in tasks: raise HTTPException(404,"task_not_found")
    return observer.list(task_id)

@app.get("/api/tasks/{task_id}/verification")
def task_verification(task_id: str):
    if task_id not in tasks: raise HTTPException(404,"task_not_found")
    return verify_task(tasks[task_id])

@app.post("/api/tasks/{task_id}/verify")
def verify_endpoint(task_id: str): return task_verification(task_id)

@app.get("/api/tasks/{task_id}/evaluation")
def task_evaluation(task_id: str):
    if task_id not in tasks: raise HTTPException(404,"task_not_found")
    return evaluate_task(tasks[task_id])

@app.post("/api/tasks/{task_id}/evaluate")
def evaluate_endpoint(task_id: str): return task_evaluation(task_id)

@app.post("/api/tasks/{task_id}/human-review")
def human_review(task_id: str, request: HumanReview):
    if task_id not in tasks: raise HTTPException(404,"task_not_found")
    return {"task_id":task_id,"approved":request.approved,"score":request.score,"confidence":request.confidence,"notes":request.notes}

@app.post("/api/tasks/{task_id}/replan")
def replan(task_id: str):
    if task_id not in tasks: raise HTTPException(404,"task_not_found")
    tasks[task_id]["plan"]=build_default_plan(tasks[task_id]["goal"]).model_dump(); tasks[task_id]["status"]="replanned"; persist(tasks[task_id]); return tasks[task_id]

@app.get("/api/history/tasks")
def history_tasks(): return store.load_tasks()
@app.get("/api/tasks/{task_id}/history")
def task_history(task_id: str): return store.load_task_history(task_id)
@app.get("/api/tasks/{task_id}/evaluations")
def task_evaluations(task_id: str): return store.list_evaluations(task_id)

@app.get("/api/memory")
def memory_list(kind: str | None = None, limit: int = Query(default=100, ge=1, le=500)): return recall("", kind=kind, limit=limit)
@app.post("/api/memory")
def memory_create(request: MemoryCreate): return remember(request.content, request.kind, request.importance, request.tags)
@app.get("/api/memory/search")
def memory_search(q: str = "", kind: str | None = None, limit: int = Query(default=20, ge=1, le=100)): return recall(q, kind=kind, limit=limit)
@app.get("/api/memory/{memory_id}")
def memory_get(memory_id: str):
    results=store.search_memories(memory_id, limit=1)
    if not results: raise HTTPException(404,"memory_not_found")
    return results[0]
@app.get("/api/storage/stats")
def storage_stats(): return store.stats()

@app.get("/api/golden")
def golden_list(): return golden_dataset.list()
@app.post("/api/golden")
def golden_create(request: GoldenCreate): return golden_dataset.add(request.name, request.goal, request.expected)
@app.delete("/api/golden/{case_id}")
def golden_delete(case_id: str): golden_dataset.remove(case_id); return {"removed":case_id}
@app.post("/api/regression/run")
def regression_run(): return regression_engine.run(evaluate_task)
@app.get("/api/regression/history")
def regression_history(): return regression_engine.history

@app.get("/api/tools")
def tools(): return list_tools()
@app.put("/api/tools/policy")
def tool_policy(request: ToolPolicy):
    set_policy(request.tool, request.policy); return list_tools()

@app.post("/api/agent/run")
async def agent_run(request: AgentRunCreate):
    run = new_run(request.goal, request.autonomy, request.max_iterations, request.max_retries, request.confidence_threshold)
    agent_runs[run["run_id"]]=run; store.save_agent_run(run)
    result=await agent_kernel.run(run); agent_runs[run["run_id"]]=result; store.save_agent_run(result); return {"run":result}

@app.get("/api/agent/runs")
def agent_run_list(): return {"runs":sorted(agent_runs.values(),key=lambda item:item.get("created_at",item.get("started_at","")),reverse=True)}
@app.get("/api/agent/{run_id}")
def agent_run_get(run_id: str):
    run=agent_runs.get(run_id) or store.get_agent_run(run_id)
    if not run: raise HTTPException(404,"agent_run_not_found")
    return run
@app.get("/api/agent/{run_id}/trace")
def agent_trace(run_id: str):
    run=agent_runs.get(run_id) or store.get_agent_run(run_id)
    if not run: raise HTTPException(404,"agent_run_not_found")
    return observer.list(run.get("task_id",run_id))
@app.post("/api/agent/{run_id}/cancel")
async def agent_cancel(run_id: str):
    run=agent_runs.get(run_id) or store.get_agent_run(run_id)
    if not run: raise HTTPException(404,"agent_run_not_found")
    run["status"]="cancelled"; executor.cancel(run.get("task_id",run_id)); store.save_agent_run(run); return run

@app.on_event("startup")
def startup():
    data=store.load_tasks()
    for task in data: tasks[task["id"]]=task
    runs=store.load_agent_runs()
    for run in runs: agent_runs[run["run_id"]]=run

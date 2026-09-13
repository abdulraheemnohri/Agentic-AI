from __future__ import annotations

import asyncio
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from . import main as core
from .agent import new_run
from .planner import build_default_plan

router = APIRouter()
_active_tasks: dict[str, asyncio.Task[Any]] = {}


def _task_payload(goal: str, autonomy: int, plan: Any, created: str, task_id: str) -> dict[str, Any]:
    return {
        "id": task_id,
        "goal": goal,
        "autonomy": autonomy,
        "status": "planned",
        "created_at": created,
        "updated_at": created,
        "plan_version": plan.version,
        "steps": [step.model_dump() for step in plan.steps],
        "events": [],
        "verification": None,
        "evaluation": None,
        "human_review": None,
        "result": None,
    }


async def _execute(run_id: str, task: dict[str, Any], run: Any) -> None:
    try:
        def persist_run(current: Any) -> None:
            core.agent_runs[current.run_id] = current.as_dict()
            core.store.save_agent_run(core.agent_runs[current.run_id])
            core.persist(task)

        final_run = await core.agent_kernel.run(task, run, persist_run)
        if task.get("evaluation"):
            core.store.save_evaluation(task["id"], task["evaluation"], core.now())
        core.persist(task)
        core.agent_runs[final_run.run_id] = final_run.as_dict()
        core.store.save_agent_run(core.agent_runs[final_run.run_id])
    except asyncio.CancelledError:
        task["status"] = "cancelled"
        core.persist(task)
        current = core.agent_runs.get(run_id)
        if current:
            current["status"] = "cancelled"
            current["phase"] = "cancelled"
            core.agent_runs[run_id] = current
            core.store.save_agent_run(current)
        raise
    except Exception as exc:
        task["status"] = "failed"
        task["result"] = f"Async agent execution failed: {exc}"
        core.emit(task["id"], "agent_background_failure", error=str(exc))
        core.persist(task)
        current = core.agent_runs.get(run_id)
        if current:
            current["status"] = "failed"
            current["phase"] = "failed"
            current["error"] = str(exc)
            core.agent_runs[run_id] = current
            core.store.save_agent_run(current)
    finally:
        _active_tasks.pop(run_id, None)


@router.post("/api/agent/run", status_code=202)
async def run_agent_async(request: core.AgentRunCreate):
    task_id, created, plan = str(uuid4()), core.now(), build_default_plan(request.goal)
    task = _task_payload(request.goal, request.autonomy, plan, created, task_id)
    core.tasks[task_id] = task
    core.emit(task_id, "agent_task_created", goal=request.goal, autonomy=request.autonomy)

    run = new_run(task, core.now, request.max_iterations, request.max_retries, request.confidence_threshold)
    core.agent_runs[run.run_id] = run.as_dict()
    core.store.save_agent_run(core.agent_runs[run.run_id])
    core.persist(task)

    background = asyncio.create_task(_execute(run.run_id, task, run), name=f"agent-run:{run.run_id}")
    _active_tasks[run.run_id] = background
    return JSONResponse(status_code=202, content={
        "accepted": True,
        "run_id": run.run_id,
        "task_id": task_id,
        "run": run.as_dict(),
        "task": task,
        "message": "Agent run accepted; execution continues asynchronously.",
    })


@router.get("/api/agent/{run_id}/async-status")
def async_status(run_id: str):
    run = core.agent_runs.get(run_id) or core.store.get_agent_run(run_id)
    if not run:
        raise HTTPException(404, "agent_run_not_found")
    task = core.tasks.get(run["task_id"])
    return {"run_id": run_id, "active": run_id in _active_tasks, "status": run.get("status"), "run": run, "task": task}

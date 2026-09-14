"""
Recovery API Routes
- Exposes endpoints for job recovery, requeue, and status.
- Integrates with the persistent job queue and recovery system.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Any, Dict, List, Optional

from .recovery import recovery_manager
from .storage import store
from .observer import observer

router = APIRouter(prefix="/api/recovery", tags=["recovery"])


@router.get("/status")
def get_recovery_status() -> Dict[str, Any]:
    """
    Get the current status of the recovery system.
    - Returns recoverable jobs, interrupted jobs, and system health.
    """
    recoverable_jobs = recovery_manager.get_recoverable_jobs()
    interrupted_jobs = recovery_manager.get_interrupted_jobs()

    return {
        "status": "healthy",
        "recoverable_jobs": len(recoverable_jobs),
        "interrupted_jobs": len(interrupted_jobs),
        "recoverable_job_ids": [job["job_id"] for job in recoverable_jobs],
        "interrupted_job_ids": [job["job_id"] for job in interrupted_jobs],
    }


@router.get("/jobs")
def list_recoverable_jobs(
    limit: int = Query(default=100, ge=1, le=1000),
    status: Optional[str] = None,
) -> Dict[str, Any]:
    """
    List all recoverable jobs.
    - Filter by status (e.g., 'queued', 'running', 'failed').
    """
    jobs = recovery_manager.get_recoverable_jobs()

    if status:
        jobs = [job for job in jobs if job.get("status") == status]

    return {
        "count": len(jobs),
        "jobs": jobs[:limit],
    }


@router.get("/jobs/{job_id}")
def get_recoverable_job(job_id: str) -> Dict[str, Any]:
    """
    Get details of a specific recoverable job.
    """
    job = recovery_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.post("/requeue/{run_id}")
def requeue_job(run_id: str) -> Dict[str, Any]:
    """
    Requeue a recoverable job for execution.
    - Only allowed for jobs in safe states (e.g., 'queued', 'failed').
    """
    job = recovery_manager.get_job_by_run_id(run_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job["status"] not in {"queued", "failed", "cancelled"}:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot requeue job in state: {job['status']}",
        )

    # Requeue the job
    success = recovery_manager.requeue_job(job["job_id"])
    if not success:
        raise HTTPException(status_code=500, detail="Failed to requeue job")

    # Log the requeue event
    observer.emit(
        job["task_id"],
        "recovery_requeued",
        run_id=run_id,
        job_id=job["job_id"],
    )

    return {
        "status": "requeued",
        "job_id": job["job_id"],
        "run_id": run_id,
        "message": "Job requeued successfully",
    }


@router.post("/resume/{run_id}")
def resume_job(run_id: str) -> Dict[str, Any]:
    """
    Resume a recoverable job from a safe state.
    - Only allowed for jobs in safe states (e.g., 'paused', 'interrupted').
    """
    job = recovery_manager.get_job_by_run_id(run_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job["status"] not in {"paused", "interrupted"}:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot resume job in state: {job['status']}",
        )

    # Resume the job
    success = recovery_manager.resume_job(job["job_id"])
    if not success:
        raise HTTPException(status_code=500, detail="Failed to resume job")

    # Log the resume event
    observer.emit(
        job["task_id"],
        "recovery_resumed",
        run_id=run_id,
        job_id=job["job_id"],
    )

    return {
        "status": "resumed",
        "job_id": job["job_id"],
        "run_id": run_id,
        "message": "Job resumed successfully",
    }


@router.post("/cancel/{run_id}")
def cancel_recoverable_job(run_id: str) -> Dict[str, Any]:
    """
    Cancel a recoverable job.
    - Only allowed for jobs in safe states (e.g., 'queued', 'paused').
    """
    job = recovery_manager.get_job_by_run_id(run_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job["status"] not in {"queued", "paused"}:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot cancel job in state: {job['status']}",
        )

    # Cancel the job
    success = recovery_manager.cancel_job(job["job_id"])
    if not success:
        raise HTTPException(status_code=500, detail="Failed to cancel job")

    # Log the cancel event
    observer.emit(
        job["task_id"],
        "recovery_cancelled",
        run_id=run_id,
        job_id=job["job_id"],
    )

    return {
        "status": "cancelled",
        "job_id": job["job_id"],
        "run_id": run_id,
        "message": "Job cancelled successfully",
    }


@router.get("/observability")
def get_recovery_observability() -> Dict[str, Any]:
    """
    Get observability data for the recovery system.
    - Returns metrics, recent events, and system health.
    """
    recoverable_jobs = recovery_manager.get_recoverable_jobs()
    interrupted_jobs = recovery_manager.get_interrupted_jobs()

    return {
        "recoverable_jobs": len(recoverable_jobs),
        "interrupted_jobs": len(interrupted_jobs),
        "recent_events": observer.get_recent_events(
            limit=50,
            event_type="recovery_requeued",
        ),
        "health": "healthy",
    }

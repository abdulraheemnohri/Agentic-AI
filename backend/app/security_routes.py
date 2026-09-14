from __future__ import annotations

from fastapi import APIRouter
from .security import security_snapshot
from .system_health import System1HealthSupervisor

router = APIRouter(prefix="/api/security", tags=["security"])
health = System1HealthSupervisor()

@router.get("/snapshot")
def snapshot():
    return security_snapshot()

@router.get("/system1-health")
def system1_health():
    return health.snapshot()

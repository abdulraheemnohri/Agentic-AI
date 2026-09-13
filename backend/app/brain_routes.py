from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from .model_adapter import list_models, runtime, set_active_model

router = APIRouter(prefix="/api/brain", tags=["brain"])

class ModelSelect(BaseModel):
    model_id: str

@router.get("/status")
def brain_status():
    return {"runtime": runtime.status(), "models": list_models(), "system1_authoritative": True}

@router.get("/models")
def brain_models():
    return {"models": list_models(), "active_model": runtime.active_model}

@router.put("/models/active")
def select_model(request: ModelSelect):
    try:
        return set_active_model(request.model_id)
    except ValueError as exc:
        raise HTTPException(404, str(exc)) from exc

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from .model_adapter import list_models, list_system1_models, register_local_system2, runtime, set_active_model, system1_review, ModelRequest

router = APIRouter(prefix="/api/brain", tags=["brain"])

class ModelSelect(BaseModel):
    model_id: str

class LocalModelRegister(BaseModel):
    model_id: str = Field(min_length=1, max_length=100)
    base_url: str = Field(min_length=1, max_length=300)
    model_name: str = Field(min_length=1, max_length=200)

class System1ReviewRequest(BaseModel):
    goal: str = Field(min_length=1, max_length=10000)
    memories: list[dict] = Field(default_factory=list)
    available_tools: list[dict] = Field(default_factory=list)
    constraints: dict = Field(default_factory=dict)
    providers: list[str] | None = None

@router.get("/status")
def brain_status():
    return {"runtime": runtime.status(), "system1": list_system1_models(), "system2": list_models(), "system1_authoritative": True, "system2_local_only": True}

@router.get("/models")
def brain_models():
    return {"system1": list_system1_models(), "system2": list_models(), "active_system2": runtime.active_system2}

@router.put("/models/active")
def select_model(request: ModelSelect):
    try:
        return set_active_model(request.model_id)
    except ValueError as exc:
        raise HTTPException(404, str(exc)) from exc

@router.post("/system2/local")
def register_local_model(request: LocalModelRegister):
    try:
        return register_local_system2(request.model_id, request.base_url, request.model_name)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc

@router.post("/system1/review")
async def system1_review_endpoint(request: System1ReviewRequest):
    return await system1_review(ModelRequest(goal=request.goal, memories=request.memories, available_tools=request.available_tools, constraints=request.constraints), request.providers)

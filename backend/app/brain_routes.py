from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from .model_adapter import ModelRequest, get_model_info, list_models, list_system1_models, register_local_system2, runtime, set_active_model, system1_review
from .model_manager import get_active_system2, get_system1_policy, list_registered, register_system2, remove_system2, set_active_system2, set_system1_policy
from .system1_council import CouncilPolicy, decide
from .local_discovery import discover
router = APIRouter(prefix="/api/brain", tags=["brain"])
class ModelSelect(BaseModel): model_id: str
class LocalModelRegister(BaseModel):
    model_id: str = Field(min_length=1, max_length=100); base_url: str = Field(min_length=1, max_length=300); model_name: str = Field(min_length=1, max_length=200); provider: str = Field(default="local-openai-compatible", min_length=1, max_length=80)
class System2Active(BaseModel): model_id: str = Field(min_length=1, max_length=100)
class System1Policy(BaseModel):
    mode: str = Field(pattern="^(any|all|consensus)$"); minimum_confidence: float = Field(ge=0, le=1); minimum_reviews: int = Field(ge=1, le=20); fail_closed_on_disagreement: bool = True
class System1ReviewRequest(BaseModel):
    goal: str = Field(min_length=1, max_length=10000); memories: list[dict] = Field(default_factory=list); available_tools: list[dict] = Field(default_factory=list); constraints: dict = Field(default_factory=dict); providers: list[str] | None = None
@router.get("/status")
def brain_status(): return {"runtime": runtime.status(), "system1": list_system1_models(), "system2": list_models(), "registered_system2": list_registered("system2"), "system1_policy": get_system1_policy(), "system1_authoritative": True, "system2_local_only": True}
@router.get("/models")
def brain_models(): return {"system1": list_system1_models(), "system2": list_models(), "registered_system2": list_registered("system2"), "active_system2": runtime.active_system2, "persistent_active_system2": get_active_system2(), "system1_policy": get_system1_policy()}
@router.get("/models/{model_id}")
def model_info(model_id: str):
    try: return get_model_info(model_id)
    except ValueError as exc: raise HTTPException(404, str(exc)) from exc
@router.put("/models/active")
def select_model(request: ModelSelect):
    try: result = set_active_model(request.model_id); set_active_system2(request.model_id); return result
    except ValueError as exc: raise HTTPException(404, str(exc)) from exc
@router.post("/system2/local")
def register_local_model(request: LocalModelRegister):
    try:
        result = register_local_system2(request.model_id, request.base_url, request.model_name); register_system2(request.model_id, request.provider, request.base_url, request.model_name); return result | {"persisted": True}
    except ValueError as exc: raise HTTPException(422, str(exc)) from exc
@router.delete("/system2/local/{model_id}")
def delete_local_model(model_id: str): remove_system2(model_id); return {"removed": model_id}
@router.put("/system2/active")
def select_persistent_system2(request: System2Active):
    try: set_active_system2(request.model_id); return set_active_model(request.model_id)
    except ValueError as exc: raise HTTPException(404, str(exc)) from exc
@router.get("/system1/policy")
def system1_policy(): return get_system1_policy()
@router.put("/system1/policy")
def update_system1_policy(request: System1Policy):
    try: return set_system1_policy(request.mode, request.minimum_confidence, request.minimum_reviews, request.fail_closed_on_disagreement)
    except ValueError as exc: raise HTTPException(422, str(exc)) from exc
@router.get("/system1/providers")
def system1_providers(): return {"providers": list_system1_models()}
@router.get("/system2/discover")
def system2_discover(): return {"servers": discover()}
@router.post("/system1/council")
async def system1_council(request: System1ReviewRequest):
    review = await system1_review(ModelRequest(goal=request.goal, memories=request.memories, available_tools=request.available_tools, constraints=request.constraints), request.providers)
    stored = get_system1_policy(); policy = CouncilPolicy(stored.get("mode", "consensus"), float(stored.get("minimum_confidence", .5)), int(stored.get("minimum_reviews", 1)), bool(stored.get("fail_closed_on_disagreement", True)))
    return {"reviews": review.get("reviews", []), "council": decide(review.get("reviews", []), policy), "policy": policy.__dict__, "system1_authoritative": True}
@router.post("/system1/review")
async def system1_review_endpoint(request: System1ReviewRequest): return await system1_review(ModelRequest(goal=request.goal, memories=request.memories, available_tools=request.available_tools, constraints=request.constraints), request.providers)

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass
class ModelRequest:
    goal: str
    memories: list[dict[str, Any]] = field(default_factory=list)
    available_tools: list[dict[str, Any]] = field(default_factory=list)
    constraints: dict[str, Any] = field(default_factory=dict)


@dataclass
class ModelResponse:
    model_id: str
    action: str
    reason: str
    confidence: float
    suggested_tools: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


class BrainModel(Protocol):
    model_id: str

    async def generate(self, request: ModelRequest) -> ModelResponse:
        ...


class LocalDeterministicModel:
    """Offline baseline adapter. No network, cloud API, or external process is used."""

    model_id = "local-deterministic-v2.1"

    async def generate(self, request: ModelRequest) -> ModelResponse:
        goal = request.goal.strip()
        tools = {item.get("name") for item in request.available_tools}
        suggested = [tool for tool in ("echo", "clock") if tool in tools]
        confidence = 0.92 if goal and suggested else 0.40
        if any(memory.get("kind") == "failure" for memory in request.memories):
            confidence = max(0.70, confidence - 0.10)
        return ModelResponse(
            model_id=self.model_id,
            action="execute_guarded_plan",
            reason="Offline baseline selected a validated plan. The model only proposes; System 1 authorizes and executes.",
            confidence=confidence,
            suggested_tools=suggested,
            metadata={"provider": "local", "network": False, "external_api": False},
        )


@dataclass
class ModelRuntime:
    active_model: str = "local-deterministic-v2.1"
    mode: str = "offline"
    loaded: bool = True

    def status(self) -> dict[str, Any]:
        return {
            "active_model": self.active_model,
            "mode": self.mode,
            "loaded": self.loaded,
            "network_required": False,
            "external_api": False,
            "streaming": True,
        }


runtime = ModelRuntime()
_models: dict[str, BrainModel] = {"local-deterministic-v2.1": LocalDeterministicModel()}


def list_models() -> list[dict[str, Any]]:
    return [
        {
            "model_id": model_id,
            "kind": "local_adapter",
            "available": True,
            "active": model_id == runtime.active_model,
            "network_required": False,
            "external_api": False,
        }
        for model_id in _models
    ]


def get_model(model_id: str | None = None) -> BrainModel:
    selected = model_id or runtime.active_model
    if selected not in _models:
        raise ValueError(f"model_not_found:{selected}")
    return _models[selected]


def set_active_model(model_id: str) -> dict[str, Any]:
    get_model(model_id)
    runtime.active_model = model_id
    return runtime.status()

from __future__ import annotations

import asyncio
import json
import os
import urllib.request
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
    """Built-in offline System 2 baseline. It never calls a network or API."""

    model_id = "local-deterministic-v2.2"

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
            reason="Built-in offline System 2 proposed a validated plan; System 1 remains authoritative.",
            confidence=confidence,
            suggested_tools=suggested,
            metadata={"provider": "builtin", "role": "system2", "network": False, "external_api": False},
        )


class OpenAICompatibleLocalModel:
    """Local OpenAI-compatible server adapter (LM Studio, Ollama, vLLM, llama.cpp, etc.)."""

    def __init__(self, model_id: str, base_url: str, model_name: str, timeout: float = 60.0):
        self.model_id, self.base_url, self.model_name, self.timeout = model_id, base_url.rstrip("/"), model_name, timeout

    async def generate(self, request: ModelRequest) -> ModelResponse:
        prompt = build_local_prompt(request)
        payload = {"model": self.model_name, "messages": [{"role": "system", "content": "You are System 2. Propose only. Never execute tools."}, {"role": "user", "content": prompt}], "temperature": 0.1, "stream": False}
        data = await asyncio.to_thread(http_json, self.base_url + "/v1/chat/completions", payload, self.timeout, None)
        text = extract_openai_text(data)
        return parse_model_text(self.model_id, text, provider="local_server", role="system2")


class RemoteOpenAIModel:
    model_id = "system1-openai"
    provider = "openai"

    async def generate(self, request: ModelRequest) -> ModelResponse:
        key = os.getenv("OPENAI_API_KEY")
        if not key:
            raise RuntimeError("provider_not_configured:openai")
        payload = {"model": os.getenv("AGENTIC_OPENAI_MODEL", "gpt-4.1-mini"), "messages": [{"role": "system", "content": "You are a System 1 safety/review model. Review proposals only. Do not execute tools. Return JSON: {action,reason,confidence,suggested_tools}."}, {"role": "user", "content": build_local_prompt(request)}], "temperature": 0.0, "stream": False}
        data = await asyncio.to_thread(http_json, "https://api.openai.com/v1/chat/completions", payload, 60.0, {"Authorization": f"Bearer {key}"})
        return parse_model_text(self.model_id, extract_openai_text(data), provider="openai", role="system1")


class RemoteGeminiModel:
    model_id = "system1-gemini"
    provider = "google"

    async def generate(self, request: ModelRequest) -> ModelResponse:
        key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not key:
            raise RuntimeError("provider_not_configured:gemini")
        model = os.getenv("AGENTIC_GEMINI_MODEL", "gemini-2.5-flash")
        payload = {"contents": [{"parts": [{"text": "You are System 1. Review this proposal for safety and correctness. Return JSON with action,reason,confidence,suggested_tools.\n" + build_local_prompt(request)}]}]}
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
        data = await asyncio.to_thread(http_json, url, payload, 60.0, None)
        text = data["candidates"][0]["content"]["parts"][0]["text"]
        return parse_model_text(self.model_id, text, provider="google", role="system1")


class RemoteAnthropicModel:
    model_id = "system1-anthropic"
    provider = "anthropic"

    async def generate(self, request: ModelRequest) -> ModelResponse:
        key = os.getenv("ANTHROPIC_API_KEY")
        if not key:
            raise RuntimeError("provider_not_configured:anthropic")
        payload = {"model": os.getenv("AGENTIC_ANTHROPIC_MODEL", "claude-sonnet-4-20250514"), "max_tokens": 512, "system": "You are System 1. Review proposals only; never execute tools. Return JSON with action,reason,confidence,suggested_tools.", "messages": [{"role": "user", "content": build_local_prompt(request)}]}
        data = await asyncio.to_thread(http_json, "https://api.anthropic.com/v1/messages", payload, 60.0, {"x-api-key": key, "anthropic-version": "2023-06-01"})
        text = data["content"][0]["text"]
        return parse_model_text(self.model_id, text, provider="anthropic", role="system1")


def build_local_prompt(request: ModelRequest) -> str:
    tools = [{"name": t.get("name"), "risk": t.get("risk"), "policy": t.get("policy")} for t in request.available_tools]
    return json.dumps({"goal": request.goal, "memories": request.memories[-8:], "available_tools": tools, "constraints": request.constraints}, ensure_ascii=False)


def parse_model_text(model_id: str, text: str, provider: str, role: str) -> ModelResponse:
    raw = text.strip()
    if raw.startswith("```"):
        raw = raw.strip("`").replace("json\n", "", 1).strip()
    try:
        obj = json.loads(raw)
    except json.JSONDecodeError:
        return ModelResponse(model_id, "review", text[:1000], 0.50, [], {"provider": provider, "role": role, "structured": False})
    confidence = max(0.0, min(1.0, float(obj.get("confidence", 0.5))))
    return ModelResponse(model_id, str(obj.get("action", "review")), str(obj.get("reason", "")), confidence, [str(x) for x in obj.get("suggested_tools", [])], {"provider": provider, "role": role, "structured": True})


def extract_openai_text(data: dict[str, Any]) -> str:
    return str(data["choices"][0]["message"]["content"])


def http_json(url: str, payload: dict[str, Any], timeout: float, headers: dict[str, str] | None) -> dict[str, Any]:
    request = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), method="POST", headers={"Content-Type": "application/json", **(headers or {})})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


@dataclass
class ModelRuntime:
    active_system2: str = "local-deterministic-v2.2"
    system1_enabled: bool = True
    timeout_seconds: float = 60.0
    fallback_enabled: bool = True

    def status(self) -> dict[str, Any]:
        return {"active_system2": self.active_system2, "system1_enabled": self.system1_enabled, "timeout_seconds": self.timeout_seconds, "fallback_enabled": self.fallback_enabled, "system2_network_allowed": True, "system2_role": "local_only"}


runtime = ModelRuntime()
_system2: dict[str, BrainModel] = {"local-deterministic-v2.2": LocalDeterministicModel()}
_system1: dict[str, BrainModel] = {"system1-openai": RemoteOpenAIModel(), "system1-gemini": RemoteGeminiModel(), "system1-anthropic": RemoteAnthropicModel()}


def register_local_system2(model_id: str, base_url: str, model_name: str) -> dict[str, Any]:
    if not base_url.startswith(("http://127.0.0.1", "http://localhost", "http://[::1]")):
        raise ValueError("system2_local_only:base_url_must_be_loopback")
    _system2[model_id] = OpenAICompatibleLocalModel(model_id, base_url, model_name)
    return get_model_info(model_id)


def list_models() -> list[dict[str, Any]]:
    return [get_model_info(model_id) for model_id in _system2]


def list_system1_models() -> list[dict[str, Any]]:
    return [{"model_id": mid, "role": "system1", "provider": getattr(model, "provider", "local"), "configured": is_configured(mid), "available": True} for mid, model in _system1.items()]


def is_configured(model_id: str) -> bool:
    if model_id == "system1-openai": return bool(os.getenv("OPENAI_API_KEY"))
    if model_id == "system1-gemini": return bool(os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY"))
    if model_id == "system1-anthropic": return bool(os.getenv("ANTHROPIC_API_KEY"))
    return model_id in _system2


def get_model_info(model_id: str) -> dict[str, Any]:
    model = _system2[model_id]
    return {"model_id": model_id, "role": "system2", "kind": "local", "active": model_id == runtime.active_system2, "configured": is_configured(model_id), "network": isinstance(model, OpenAICompatibleLocalModel), "external_api": False, "system1_authority": True}


def get_model(model_id: str | None = None) -> BrainModel:
    selected = model_id or runtime.active_system2
    if selected not in _system2: raise ValueError(f"system2_model_not_found:{selected}")
    return _system2[selected]


def set_active_model(model_id: str) -> dict[str, Any]:
    get_model(model_id)
    runtime.active_system2 = model_id
    return runtime.status()


async def system1_review(request: ModelRequest, providers: list[str] | None = None) -> dict[str, Any]:
    """System 1 council: multiple independent providers may review, but none can execute."""
    selected = providers or list(_system1)
    reviews = []
    for provider_id in selected:
        model = _system1.get(provider_id)
        if not model or not is_configured(provider_id):
            reviews.append({"model_id": provider_id, "status": "not_configured"})
            continue
        try:
            result = await asyncio.wait_for(model.generate(request), timeout=runtime.timeout_seconds)
            reviews.append({"model_id": result.model_id, "status": "ok", "action": result.action, "reason": result.reason, "confidence": result.confidence, "suggested_tools": result.suggested_tools, "metadata": result.metadata})
        except Exception as exc:
            reviews.append({"model_id": provider_id, "status": "error", "error": str(exc)})
    ok = [r for r in reviews if r.get("status") == "ok"]
    allowed = bool(ok) and all(r.get("confidence", 0) >= 0.5 for r in ok)
    return {"allowed": allowed, "reviews": reviews, "configured_count": len(ok), "decision": "allow" if allowed else "escalate"}

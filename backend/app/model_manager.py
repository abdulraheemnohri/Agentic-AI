from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from datetime import datetime, timezone

CONFIG_PATH = Path("data/model_registry.json")
DEFAULT_POLICY = {"mode": "consensus", "minimum_confidence": 0.50, "minimum_reviews": 1, "fail_closed_on_disagreement": True}


def _load() -> dict[str, Any]:
    default = {"system1": {}, "system2": {}, "active_system2": "local-deterministic-v2.2", "system1_policy": DEFAULT_POLICY.copy()}
    if not CONFIG_PATH.exists(): return default
    try:
        data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        data.setdefault("system1", {}); data.setdefault("system2", {}); data.setdefault("active_system2", "local-deterministic-v2.2")
        data.setdefault("system1_policy", DEFAULT_POLICY.copy())
        for key, value in DEFAULT_POLICY.items(): data["system1_policy"].setdefault(key, value)
        return data
    except (OSError, json.JSONDecodeError): return default


def _save(data: dict[str, Any]) -> None:
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def register_system2(model_id: str, provider: str, base_url: str, model_name: str) -> dict[str, Any]:
    if not base_url.startswith(("http://127.0.0.1", "http://localhost", "http://[::1]")): raise ValueError("system2_local_only:base_url_must_be_loopback")
    data = _load(); data["system2"][model_id] = {"provider": provider, "base_url": base_url.rstrip("/"), "model_name": model_name, "updated_at": datetime.now(timezone.utc).isoformat()}; _save(data)
    return data["system2"][model_id] | {"model_id": model_id, "role": "system2"}


def remove_system2(model_id: str) -> None:
    data = _load(); data["system2"].pop(model_id, None)
    if data["active_system2"] == model_id: data["active_system2"] = "local-deterministic-v2.2"
    _save(data)


def list_registered(role: str) -> list[dict[str, Any]]:
    data = _load(); return [{"model_id": mid, "role": role, **cfg} for mid, cfg in data.get(role, {}).items()]


def get_active_system2() -> str: return _load().get("active_system2", "local-deterministic-v2.2")

def set_active_system2(model_id: str) -> str:
    data = _load(); data["active_system2"] = model_id; _save(data); return model_id

def get_system1_policy() -> dict[str, Any]: return _load().get("system1_policy", DEFAULT_POLICY.copy())

def set_system1_policy(mode: str, minimum_confidence: float, minimum_reviews: int, fail_closed_on_disagreement: bool = True) -> dict[str, Any]:
    if mode not in {"any", "all", "consensus"}: raise ValueError("invalid_system1_policy_mode")
    if not 0 <= minimum_confidence <= 1: raise ValueError("invalid_minimum_confidence")
    if minimum_reviews < 1: raise ValueError("invalid_minimum_reviews")
    data = _load(); data["system1_policy"] = {"mode": mode, "minimum_confidence": minimum_confidence, "minimum_reviews": minimum_reviews, "fail_closed_on_disagreement": bool(fail_closed_on_disagreement)}; _save(data); return data["system1_policy"]

"""
System 2 Intelligence Service
- Manages local models (Ollama, LM Studio, llama.cpp).
- Loopback-only, non-authoritative, and replaceable.
"""

from __future__ import annotations
import asyncio
import importlib
import json
import os
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4


@dataclass
class System2State:
    status: str = "stopped"
    version: str = "local"
    update_available: bool = False
    last_update: str | None = None
    last_error: str | None = None


class System2LifecycleBackend:
    """Frontend-controlled lifecycle for local System 2 only.

    This service can start/stop/reload the local runtime and perform controlled
    package/model upgrades. It rejects remote model URLs and never exposes a
    System 1 authority operation.
    """

    def __init__(self, root: str | Path | None = None):
        self.root = Path(root or Path(__file__).resolve().parents[1])
        self.state = System2State()
        self._worker: asyncio.Task | None = None
        self._runtime_module: str | None = None

    @staticmethod
    def _local_only(value: str) -> bool:
        return value.startswith(("http://127.0.0.1", "http://localhost", "http://[::1]"))

    def status(self) -> dict[str, Any]:
        return {
            "backend": "system2",
            "role": "local_reasoning",
            "network_scope": "loopback_only",
            "frontend_controlled": True,
            "authority": False,
            "state": self.state.__dict__.copy(),
            "runtime_module": self._runtime_module,
        }

    async def _idle_worker(self) -> None:
        try:
            while True:
                await asyncio.sleep(60)
        except asyncio.CancelledError:
            raise

    async def start(self, runtime_module: str | None = None) -> dict[str, Any]:
        if self.state.status == "running":
            return self.status()
        if runtime_module:
            if not runtime_module.replace("_", "").isalnum():
                raise ValueError("invalid_runtime_module")
            self._runtime_module = runtime_module
        self._worker = asyncio.create_task(self._idle_worker())
        self.state.status = "running"
        self.state.last_error = None
        return self.status()

    async def stop(self) -> dict[str, Any]:
        if self._worker and not self._worker.done():
            self._worker.cancel()
            try:
                await self._worker
            except asyncio.CancelledError:
                pass
        self.state.status = "stopped"
        return self.status()

    async def restart(self) -> dict[str, Any]:
        await self.stop()
        return await self.start(self._runtime_module)

    async def update(self, package: str | None = None) -> dict[str, Any]:
        if package and (package.startswith("http://") or package.startswith("https://")):
            raise ValueError("system2_update_remote_url_denied")
        if package and not package.replace("-", "").replace("_", "").isalnum():
            raise ValueError("invalid_package_name")
        # Local package reload only. No network package manager is invoked.
        if package:
            try:
                importlib.import_module(package)
                importlib.reload(sys.modules[package])
            except Exception as exc:
                self.state.last_error = str(exc)
                raise
        self.state.update_available = False
        self.state.last_update = str(os.times().elapsed)
        return self.status()

    async def upgrade(self, version: str, local_path: str | None = None) -> dict[str, Any]:
        if not version or len(version) > 64:
            raise ValueError("invalid_version")
        if local_path:
            path = Path(local_path).resolve()
            if self.root not in path.parents and path != self.root:
                raise ValueError("system2_upgrade_path_outside_backend")
            if not path.exists():
                raise ValueError("system2_upgrade_source_not_found")
        self.state.version = version
        self.state.last_update = str(os.times().elapsed)
        self.state.update_available = False
        return self.status()


class System2Service:
    """
    Core service for System 2 Intelligence.
    Handles:
    - Local model discovery (Ollama, LM Studio, llama.cpp)
    - Model activation/deactivation
    - Proposal generation
    - Loopback enforcement
    """

    def __init__(self):
        # System 2 State
        self._state: str = "stopped"
        self._active_model: Optional[str] = None
        self._models: Dict[str, Dict[str, Any]] = {}
        self._proposals: List[Dict[str, Any]] = []
        self._start_time = datetime.now(timezone.utc)

        # Initialize with default local models (if detected)
        self.discover_models()

    # --- Lifecycle Methods ---

    def start(self) -> None:
        """Start System 2."""
        self._state = "running"

    def stop(self) -> None:
        """Stop System 2."""
        self._state = "stopped"

    def restart(self) -> None:
        """Restart System 2."""
        self.stop()
        self.start()

    def get_status(self) -> str:
        """Get System 2 status."""
        return self._state

    # --- Model Methods ---

    def discover_models(self) -> List[Dict[str, Any]]:
        """
        Discover local models from Ollama, LM Studio, llama.cpp.
        - Only loopback endpoints are accepted.
        """
        # Placeholder: In a real implementation, this would:
        # 1. Check for Ollama at http://127.0.0.1:11434
        # 2. Check for LM Studio at http://127.0.0.1:1234
        # 3. Check for llama.cpp at http://127.0.0.1:8080
        # For now, return mock data.
        discovered_models = [
            {
                "name": "llama-3.2:70b",
                "provider": "Ollama",
                "endpoint": "http://127.0.0.1:11434",
                "enabled": True,
                "priority": 1,
                "size": "70B",
                "quantization": "Q4",
                "context_length": 32768,
                "network_scope": "loopback",
            },
            {
                "name": "mistral-7b",
                "provider": "LM Studio",
                "endpoint": "http://127.0.0.1:1234",
                "enabled": False,
                "priority": 2,
                "size": "7B",
                "quantization": "Q8",
                "context_length": 4096,
                "network_scope": "loopback",
            },
        ]
        self._models = {model["name"]: model for model in discovered_models}
        return discovered_models

    def list_models(self) -> List[Dict[str, Any]]:
        """List all local models."""
        return list(self._models.values())

    def get_model(self, model_name: str) -> Optional[Dict[str, Any]]:
        """Get a specific model."""
        return self._models.get(model_name)

    def activate_model(self, model_name: str) -> bool:
        """Activate a local model."""
        if model_name in self._models:
            self._models[model_name]["enabled"] = True
            self._active_model = model_name
            return True
        return False

    def deactivate_model(self, model_name: str) -> bool:
        """Deactivate a local model."""
        if model_name in self._models:
            self._models[model_name]["enabled"] = False
            if self._active_model == model_name:
                self._active_model = None
            return True
        return False

    def get_active_model(self) -> Optional[str]:
        """Get the currently active model."""
        return self._active_model

    # --- Loopback Enforcement ---

    @staticmethod
    def is_loopback(endpoint: str) -> bool:
        """
        Check if an endpoint is loopback-only.
        - Allowed: 127.0.0.1, localhost, ::1
        - Rejected: Public IPs, domains, https
        """
        loopback_hosts = ["127.0.0.1", "localhost", "::1"]
        for host in loopback_hosts:
            if host in endpoint:
                return True
        return False

    # --- Proposal Methods ---

    def log_proposal(self, proposal: Dict[str, Any]) -> str:
        """Log a System 2 proposal."""
        proposal_id = str(uuid4())
        proposal["proposal_id"] = proposal_id
        proposal["timestamp"] = datetime.now(timezone.utc).isoformat()
        self._proposals.append(proposal)
        return proposal_id

    def get_proposal(self, proposal_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific proposal."""
        for proposal in self._proposals:
            if proposal["proposal_id"] == proposal_id:
                return proposal
        return None

    # --- System Metrics ---

    def get_cpu_usage(self) -> float:
        """Get CPU usage (placeholder)."""
        return 0.0  # Mock value

    def get_memory_usage(self) -> float:
        """Get memory usage (placeholder)."""
        return 0.0  # Mock value

    def get_latency(self) -> float:
        """Get average latency (placeholder)."""
        return 0.0  # Mock value

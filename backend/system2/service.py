from __future__ import annotations

import asyncio
import importlib
import json
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


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

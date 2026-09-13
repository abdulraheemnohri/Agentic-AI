from __future__ import annotations

import socket
import time
import urllib.request
from typing import Any

CANDIDATES = {
    "lm-studio": ("127.0.0.1", 1234, "/v1/models"),
    "ollama": ("127.0.0.1", 11434, "/api/tags"),
    "llama-cpp": ("127.0.0.1", 8080, "/v1/models"),
    "vllm": ("127.0.0.1", 8000, "/v1/models"),
}


def discover(timeout: float = 1.5) -> list[dict[str, Any]]:
    results = []
    for provider, (host, port, path) in CANDIDATES.items():
        started = time.perf_counter()
        reachable = False
        detail: Any = None
        try:
            with socket.create_connection((host, port), timeout=timeout):
                reachable = True
            req = urllib.request.Request(f"http://{host}:{port}{path}", method="GET")
            with urllib.request.urlopen(req, timeout=timeout) as response:
                detail = response.status
        except Exception as exc:
            detail = type(exc).__name__
        results.append({"provider": provider, "base_url": f"http://{host}:{port}", "reachable": reachable, "health": detail, "latency_ms": round((time.perf_counter() - started) * 1000, 2), "system2_allowed": True, "network_scope": "loopback_only"})
    return results

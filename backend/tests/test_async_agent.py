import pytest
from fastapi.testclient import TestClient

from backend.app.server import app


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


def test_agent_run_returns_202_and_run_id(client):
    response = client.post("/api/agent/run", json={"goal": "say hello", "autonomy": 1})
    assert response.status_code == 202
    body = response.json()
    assert body["accepted"] is True
    assert body["run_id"]
    assert body["task_id"]
    status = client.get(f"/api/agent/{body['run_id']}/async-status")
    assert status.status_code == 200
    assert status.json()["run_id"] == body["run_id"]


def test_legacy_sync_route_is_not_registered():
    post_paths = {
        route.path
        for route in app.routes
        if "POST" in getattr(route, "methods", set())
    }
    assert "/api/agent/run" in post_paths
    assert sum(
        1 for route in app.routes
        if route.path == "/api/agent/run" and "POST" in getattr(route, "methods", set())
    ) == 1


def test_backend_control_is_mounted(client):
    response = client.get("/api/backends/status")
    assert response.status_code == 200
    assert response.json()["system1"]["always_on"] is True

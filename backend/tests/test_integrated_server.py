import pytest

from backend.app.server import app
from backend.system_backends import system1_backend, system2_backend


def test_integrated_app_mounts_backend_routes():
    paths = {route.path for route in app.routes}
    assert "/api/backends/status" in paths
    assert "/api/backends/system1" in paths
    assert "/api/backends/system2" in paths
    assert "/api/backends/system2/start" in paths
    assert "/api/backends/system2/stop" in paths
    assert "/api/backends/system2/update" in paths
    assert "/api/backends/system2/upgrade" in paths


@pytest.mark.asyncio
async def test_system1_is_not_frontend_stoppable():
    with pytest.raises(RuntimeError, match="manual_stop_not_allowed"):
        system1_backend.stop()


@pytest.mark.asyncio
async def test_system2_is_frontend_lifecycle_controlled():
    await system2_backend.stop()
    started = await system2_backend.start()
    assert started["state"]["status"] == "running"
    stopped = await system2_backend.stop()
    assert stopped["state"]["status"] == "stopped"

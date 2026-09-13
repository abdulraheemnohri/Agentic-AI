import pytest

from app.system1.service import System1AutomaticBackend
from app.system2.service import System2LifecycleBackend


def test_system1_cannot_be_manually_stopped():
    backend = System1AutomaticBackend()
    with pytest.raises(RuntimeError, match="always_on"):
        backend.stop()


@pytest.mark.asyncio
async def test_system2_frontend_lifecycle():
    backend = System2LifecycleBackend()
    assert (await backend.start())["state"]["status"] == "running"
    assert (await backend.stop())["state"]["status"] == "stopped"


@pytest.mark.asyncio
async def test_system2_rejects_remote_update():
    backend = System2LifecycleBackend()
    with pytest.raises(ValueError, match="remote_url"):
        await backend.update("https://example.com/model.whl")


@pytest.mark.asyncio
async def test_system2_upgrade_is_local_controlled():
    backend = System2LifecycleBackend()
    result = await backend.upgrade("v2.8.1")
    assert result["state"]["version"] == "v2.8.1"

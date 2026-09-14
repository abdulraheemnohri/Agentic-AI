import asyncio

import pytest

from backend.app.runtime import ExecutionRuntime


@pytest.mark.asyncio
async def test_runtime_executes_job_and_tracks_completion(tmp_path):
    runtime = ExecutionRuntime(tmp_path)
    seen = []

    async def work():
        await asyncio.sleep(0)
        seen.append(True)
        return "ok"

    task = await runtime.submit("job-1", work)
    assert await task == "ok"
    assert seen == [True]
    assert runtime.status()["completed"] == 1
    assert runtime.status()["active_jobs"] == 0


def test_runtime_config_is_persisted(tmp_path):
    runtime = ExecutionRuntime(tmp_path)
    cfg = runtime.save_config(max_concurrency=4, queue_limit=9, poll_interval_ms=250)
    assert cfg.max_concurrency == 4
    assert cfg.queue_limit == 9
    assert cfg.poll_interval_ms == 250
    restored = ExecutionRuntime(tmp_path)
    assert restored.config.max_concurrency == 4
    assert restored.config.queue_limit == 9


@pytest.mark.asyncio
async def test_runtime_rejects_when_capacity_and_queue_are_full(tmp_path):
    runtime = ExecutionRuntime(tmp_path)
    runtime.save_config(max_concurrency=1, queue_limit=1)
    gate = asyncio.Event()

    async def work():
        await gate.wait()

    first = await runtime.submit("one", work)
    second = await runtime.submit("two", work)
    with pytest.raises(RuntimeError, match="runtime_queue_full"):
        await runtime.submit("three", work)
    gate.set()
    await asyncio.gather(first, second)

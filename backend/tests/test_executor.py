import asyncio

import pytest

from app.executor import Executor
from app.observer import Observer


def test_echo_execution():
    observer = Observer()
    executor = Executor(observer, lambda: "2026-01-01T00:00:00+00:00")
    task = {"id": "t1", "goal": "hello", "autonomy": 1}
    step = {"id": "s1", "tool": "echo", "retry_count": 0, "timeout_seconds": 2}
    result = asyncio.run(executor.execute_step(task, step))
    assert result.status == "completed"
    assert result.output == {"text": "hello"}
    assert observer.list("t1")[1]["type"] == "step_started"


def test_denied_tool_is_blocked():
    observer = Observer()
    executor = Executor(observer, lambda: "now")
    task = {"id": "t2", "goal": "hello", "autonomy": 1}
    step = {"id": "s1", "tool": "echo", "retry_count": 0, "timeout_seconds": 2}
    # Disabled/deny behavior is owned by the registry; simulate a bad tool here.
    step["tool"] = "missing"
    result = asyncio.run(executor.execute_step(task, step))
    assert result.status == "blocked"


def test_retry_count_retries_tool_failure():
    observer = Observer()
    executor = Executor(observer, lambda: "now")
    executor._dispatch = lambda tool, goal: (_ for _ in ()).throw(RuntimeError("boom"))
    task = {"id": "t3", "goal": "hello", "autonomy": 1}
    step = {"id": "s1", "tool": "echo", "retry_count": 2, "timeout_seconds": 2}
    result = asyncio.run(executor.execute_step(task, step))
    assert result.status == "failed"
    assert result.attempts == 3
    assert any(event["type"] == "step_retrying" for event in observer.list("t3"))


def test_cancellation():
    observer = Observer()
    executor = Executor(observer, lambda: "now")
    executor.cancel("t4")
    task = {"id": "t4", "goal": "hello", "autonomy": 1}
    step = {"id": "s1", "tool": "echo", "retry_count": 0, "timeout_seconds": 2}
    result = asyncio.run(executor.execute_step(task, step))
    assert result.status == "cancelled"

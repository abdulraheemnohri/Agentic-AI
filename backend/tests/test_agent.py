import pytest
from app.agent import AgentKernel, new_run
from app.executor import Executor
from app.observer import Observer

@pytest.mark.asyncio
async def test_agent_loop_completes():
    observer=Observer(); now=lambda:"2026-01-01T00:00:00+00:00"; kernel=AgentKernel(Executor(observer,now),observer,now)
    task={"id":"t1","goal":"say hello","autonomy":1,"status":"planned","plan_version":1,"steps":[]}
    run=new_run(task,now); saved=[]; result=await kernel.run(task,run,lambda r:saved.append(r.as_dict()))
    assert result.status=="completed"; assert result.phase=="completed"; assert task["status"]=="completed"; assert task["verification"]["passed"] is True; assert result.decisions; assert saved

@pytest.mark.asyncio
async def test_system2_cannot_bypass_permission():
    observer=Observer(); now=lambda:"2026-01-01T00:00:00+00:00"; kernel=AgentKernel(Executor(observer,now),observer,now)
    task={"id":"t2","goal":"blocked","autonomy":0,"status":"planned","plan_version":1,"steps":[{"id":"s","title":"unsafe","tool":"unknown-tool","status":"pending"}]}
    run=new_run(task,now); result=await kernel.run(task,run,lambda r:None)
    assert result.status=="escalated"; assert result.error=="system1_permission_denied_or_escalated"; assert task["status"]=="escalated"

def test_run_limits_are_clamped():
    task={"id":"t3","goal":"x"}; now=lambda:"2026-01-01T00:00:00+00:00"; run=new_run(task,now,max_iterations=999,max_retries=999,confidence_threshold=2)
    assert run.max_iterations==20; assert run.max_retries==10; assert run.confidence_threshold==1.0

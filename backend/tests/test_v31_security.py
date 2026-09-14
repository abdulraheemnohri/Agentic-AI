import asyncio
from backend.app.recovery import RecoveryManager
from backend.app.security import security_snapshot, validate_system2_action


def test_system2_has_no_authority():
    s = security_snapshot()
    assert s['system1']['authority'] is True
    assert s['system1']['frontend_stop_allowed'] is False
    assert s['system2']['authority'] is False
    assert s['system2']['network_scope'] == 'loopback_only'
    try:
        validate_system2_action('stop_system1')
    except PermissionError:
        pass
    else:
        raise AssertionError('System 2 authority bypassed')


def test_recovery_and_audit(tmp_path):
    async def run():
        r = RecoveryManager(tmp_path / 'runtime.db')
        await r.register('r1','t1')
        await r.update('r1','running','reasoning')
        await r.audit('execution_started','system1','r1','t1',phase='reasoning')
        assert r.recoverable()[0]['run_id'] == 'r1'
        assert r.audit_list(10)[0]['event_type'] == 'execution_started'
    asyncio.run(run())

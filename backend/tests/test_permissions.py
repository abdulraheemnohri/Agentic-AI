import pytest

from app.tool_registry import authorization, set_policy


def test_disabled_tool_is_blocked():
    set_policy("echo", enabled=False)
    allowed, reason = authorization("echo", autonomy=5)
    assert not allowed
    assert reason == "tool_disabled"
    set_policy("echo", enabled=True)


def test_confirm_policy_requires_approval():
    set_policy("echo", policy="CONFIRM")
    assert authorization("echo", autonomy=5)[0] is False
    assert authorization("echo", autonomy=5, approved=True)[0] is True
    set_policy("echo", policy="AUTO")


def test_deny_policy_always_blocks():
    set_policy("echo", policy="DENY")
    assert authorization("echo", autonomy=5, approved=True) == (False, "policy_denied")
    set_policy("echo", policy="AUTO")


def test_invalid_policy_is_rejected():
    with pytest.raises(ValueError, match="invalid_policy"):
        set_policy("echo", policy="INVALID")

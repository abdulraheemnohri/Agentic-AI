from __future__ import annotations

from typing import Any


FORBIDDEN_SYSTEM2_ACTIONS = frozenset({"authorize_system1", "modify_system1", "stop_system1", "replace_system1"})


def validate_system2_action(action: str) -> None:
    if action.strip().lower() in FORBIDDEN_SYSTEM2_ACTIONS:
        raise PermissionError("system2_authority_denied")


def security_snapshot() -> dict[str, Any]:
    return {
        "system1": {"authority": True, "always_on": True, "frontend_stop_allowed": False, "system2_control_allowed": False},
        "system2": {"authority": False, "network_scope": "loopback_only", "frontend_controlled": True},
        "execution_gate": "system1_council_then_tool_permissions",
        "remote_system2_fallback": False,
    }

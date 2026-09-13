from __future__ import annotations

from dataclasses import dataclass
from typing import Any

RISK_LEVELS = ("SAFE", "LOW", "MEDIUM", "HIGH", "CRITICAL")
POLICIES = ("AUTO", "CONFIRM", "DENY")

@dataclass
class ToolDefinition:
    name: str
    description: str
    risk: str = "SAFE"
    policy: str = "AUTO"
    enabled: bool = True

    def as_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "risk": self.risk,
            "policy": self.policy,
            "enabled": self.enabled,
        }

TOOLS: dict[str, ToolDefinition] = {
    "echo": ToolDefinition("echo", "Return supplied text.", "SAFE", "AUTO"),
    "clock": ToolDefinition("clock", "Read server UTC time.", "SAFE", "AUTO"),
}


def list_tools() -> list[dict[str, Any]]:
    return [tool.as_dict() for tool in TOOLS.values()]


def get_tool(name: str) -> ToolDefinition | None:
    return TOOLS.get(name)


def set_policy(name: str, policy: str | None = None, enabled: bool | None = None, risk: str | None = None) -> ToolDefinition:
    tool = TOOLS.get(name)
    if tool is None:
        raise KeyError(name)
    if policy is not None:
        if policy not in POLICIES:
            raise ValueError("invalid_policy")
        tool.policy = policy
    if risk is not None:
        if risk not in RISK_LEVELS:
            raise ValueError("invalid_risk")
        tool.risk = risk
    if enabled is not None:
        tool.enabled = enabled
    return tool


def authorization(name: str, autonomy: int, approved: bool = False) -> tuple[bool, str]:
    tool = get_tool(name)
    if tool is None:
        return False, "unknown_tool"
    if not tool.enabled:
        return False, "tool_disabled"
    if tool.policy == "DENY":
        return False, "policy_denied"
    if tool.policy == "CONFIRM" and not approved:
        return False, "approval_required"
    if tool.risk == "CRITICAL":
        return False, "critical_tool_blocked_in_v1"
    if tool.risk == "HIGH" and autonomy < 4 and not approved:
        return False, "high_risk_confirmation_required"
    if tool.risk == "MEDIUM" and autonomy < 2 and not approved:
        return False, "medium_risk_confirmation_required"
    return True, "authorized"

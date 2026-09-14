"""
System 1 Authority Service
- Manages Council, Security, Providers, and Audit for Agentic-AI.
- Never modifiable by System 2 or frontend.
"""

from __future__ import annotations
import asyncio
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Awaitable, Callable, Dict, List, Optional
from uuid import uuid4


@dataclass
class System1State:
    running: bool = False
    cycles: int = 0
    last_cycle_at: str | None = None
    last_error: str | None = None


class System1AutomaticBackend:
    """Always-on authority supervisor.

    System 1 owns policy, health checks and authorization. It never delegates
    authority to System 2 and can continue with the built-in guard when remote
    providers are unavailable.
    """

    def __init__(self, cycle_seconds: float = 5.0):
        self.cycle_seconds = max(1.0, cycle_seconds)
        self.state = System1State()
        self._task: asyncio.Task | None = None
        self._reviewer: Callable[[], Awaitable[dict[str, Any]]] | None = None

    def bind_reviewer(self, reviewer: Callable[[], Awaitable[dict[str, Any]]]) -> None:
        self._reviewer = reviewer

    def status(self) -> dict[str, Any]:
        return {
            "backend": "system1",
            "role": "authoritative_control_plane",
            "always_on": True,
            "running": self.state.running,
            "cycles": self.state.cycles,
            "last_cycle_at": self.state.last_cycle_at,
            "last_error": self.state.last_error,
            "cycle_seconds": self.cycle_seconds,
            "remote_fallback": "builtin_system1_guard",
            "system2_authority": False,
        }

    async def _cycle(self) -> None:
        self.state.cycles += 1
        self.state.last_cycle_at = datetime.now(timezone.utc).isoformat()
        self.state.last_error = None
        if self._reviewer:
            try:
                await self._reviewer()
            except Exception as exc:
                self.state.last_error = str(exc)

    async def _loop(self) -> None:
        self.state.running = True
        try:
            while True:
                await self._cycle()
                await asyncio.sleep(self.cycle_seconds)
        except asyncio.CancelledError:
            self.state.running = False
            raise

    def start(self) -> None:
        if self._task and not self._task.done():
            return
        self._task = asyncio.create_task(self._loop())

    def stop(self) -> None:
        # Public stop is intentionally disabled: System 1 must remain automatic.
        raise RuntimeError("system1_always_on:manual_stop_not_allowed")

    async def shutdown(self) -> None:
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        self.state.running = False


class System1Service:
    """
    Core service for System 1 Authority.
    Handles:
    - Council voting logic
    - Provider management
    - Security rules
    - Audit logging
    """

    def __init__(self):
        # Council Configuration
        self.council_mode: str = "Consensus"  # Options: Any, All, Consensus
        self.minimum_confidence: float = 0.7
        self.minimum_reviews: int = 2
        self.fail_closed_on_disagreement: bool = True
        self.eligible_reviewers: List[str] = ["OpenAI", "Gemini", "Anthropic", "Built-in Guard"]
        self._votes: List[Dict[str, Any]] = []  # Store recent votes

        # Providers
        self._providers: Dict[str, Dict[str, Any]] = {
            "OpenAI": {
                "name": "OpenAI",
                "enabled": True,
                "model": "gpt-4",
                "timeout": 30,
                "priority": 1,
                "healthy": True,
                "calls": 0,
                "successes": 0,
                "errors": 0,
                "latency": 0.0,
                "last_status": "healthy",
                "last_error": None,
            },
            "Gemini": {
                "name": "Gemini",
                "enabled": True,
                "model": "gemini-pro",
                "timeout": 30,
                "priority": 1,
                "healthy": True,
                "calls": 0,
                "successes": 0,
                "errors": 0,
                "latency": 0.0,
                "last_status": "healthy",
                "last_error": None,
            },
            "Anthropic": {
                "name": "Anthropic",
                "enabled": True,
                "model": "claude-3",
                "timeout": 30,
                "priority": 1,
                "healthy": True,
                "calls": 0,
                "successes": 0,
                "errors": 0,
                "latency": 0.0,
                "last_status": "healthy",
                "last_error": None,
            },
            "Built-in Guard": {
                "name": "Built-in Guard",
                "enabled": True,
                "model": "guard-v1",
                "timeout": 10,
                "priority": 0,  # Lowest priority (fallback)
                "healthy": True,
                "calls": 0,
                "successes": 0,
                "errors": 0,
                "latency": 0.0,
                "last_status": "healthy",
                "last_error": None,
            },
        }

        # Audit Logs
        self._audit_events: List[Dict[str, Any]] = []

        # Uptime Tracking
        self._start_time = datetime.now(timezone.utc)

    # --- Council Methods ---

    def cast_vote(
        self,
        reviewer: str,
        decision: str,
        confidence: float,
        reason: str,
    ) -> Dict[str, Any]:
        """
        Cast a vote in the Council.
        Returns the final decision based on the Council mode.
        """
        if reviewer not in self.eligible_reviewers:
            raise ValueError(f"Reviewer '{reviewer}' is not eligible to vote.")

        if decision not in {"ALLOW", "DENY", "ESCALATE"}:
            raise ValueError(f"Invalid decision: {decision}. Must be ALLOW, DENY, or ESCALATE.")

        # Log the vote
        vote_id = str(uuid4())
        vote = {
            "vote_id": vote_id,
            "reviewer": reviewer,
            "decision": decision,
            "confidence": confidence,
            "reason": reason,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self._votes.append(vote)

        # Determine final decision based on Council mode
        if self.council_mode == "Any":
            # Any single ALLOW is sufficient
            final_decision = "ALLOW" if decision == "ALLOW" else "DENY"
            allowed = final_decision == "ALLOW"
        elif self.council_mode == "All":
            # All must ALLOW (not implemented here; requires tracking all votes)
            final_decision = "DENY"  # Placeholder
            allowed = False
        else:  # Consensus
            # Weighted decision (simplified: majority ALLOW)
            allow_votes = [v for v in self._votes if v["decision"] == "ALLOW"]
            deny_votes = [v for v in self._votes if v["decision"] == "DENY"]
            if len(allow_votes) > len(deny_votes):
                final_decision = "ALLOW"
                allowed = True
            else:
                final_decision = "DENY"
                allowed = False

        # Log the Council decision in audit
        self.log_audit_event(
            actor="Council",
            action="council_decision",
            result=final_decision,
            risk="HIGH",
            metadata={"vote_id": vote_id, "reviewer": reviewer, "decision": decision},
        )

        return {
            "vote_id": vote_id,
            "decision": final_decision,
            "allowed": allowed,
            "confidence": confidence,
            "votes": self._votes,
            "timestamp": vote["timestamp"],
        }

    def get_council_status(self) -> Dict[str, Any]:
        """Get current Council status."""
        return {
            "mode": self.council_mode,
            "minimum_confidence": self.minimum_confidence,
            "minimum_reviews": self.minimum_reviews,
            "fail_closed_on_disagreement": self.fail_closed_on_disagreement,
        }

    def get_recent_votes(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent Council votes."""
        return self._votes[-limit:]

    # --- Provider Methods ---

    def list_providers(self) -> List[Dict[str, Any]]:
        """List all providers."""
        return list(self._providers.values())

    def get_provider(self, provider_name: str) -> Optional[Dict[str, Any]]:
        """Get a specific provider."""
        return self._providers.get(provider_name)

    def enable_provider(self, provider_name: str) -> bool:
        """Enable a provider."""
        if provider_name in self._providers:
            self._providers[provider_name]["enabled"] = True
            self.log_audit_event(
                actor="System1",
                action="provider_enabled",
                result="SUCCESS",
                risk="LOW",
                metadata={"provider": provider_name},
            )
            return True
        return False

    def disable_provider(self, provider_name: str) -> bool:
        """Disable a provider."""
        if provider_name in self._providers:
            self._providers[provider_name]["enabled"] = False
            self.log_audit_event(
                actor="System1",
                action="provider_disabled",
                result="SUCCESS",
                risk="MEDIUM",
                metadata={"provider": provider_name},
            )
            return True
        return False

    def get_provider_status(self) -> Dict[str, Any]:
        """Get status of all providers."""
        return {
            provider: {
                "healthy": data["healthy"],
                "enabled": data["enabled"],
                "calls": data["calls"],
                "successes": data["successes"],
                "errors": data["errors"],
            }
            for provider, data in self._providers.items()
        }

    # --- Security Methods ---

    def get_security_status(self) -> Dict[str, Any]:
        """Get current security status."""
        return {
            "system1_authority": True,
            "system1_always_on": True,
            "system2_authority": False,
            "system2_loopback_only": True,
            "remote_system2_fallback": False,
        }

    # --- Audit Methods ---

    def log_audit_event(
        self,
        actor: str,
        action: str,
        run_id: Optional[str] = None,
        task_id: Optional[str] = None,
        result: str = "SUCCESS",
        risk: str = "LOW",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Log an audit event."""
        event_id = str(uuid4())
        event = {
            "event_id": event_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "actor": actor,
            "action": action,
            "run_id": run_id,
            "task_id": task_id,
            "result": result,
            "risk": risk,
            "metadata": metadata or {},
        }
        self._audit_events.append(event)
        return event_id

    def list_audit_events(
        self,
        limit: int = 100,
        actor: Optional[str] = None,
        action: Optional[str] = None,
        risk: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """List audit events with filters."""
        events = self._audit_events[-limit:]
        if actor:
            events = [e for e in events if e["actor"] == actor]
        if action:
            events = [e for e in events if e["action"] == action]
        if risk:
            events = [e for e in events if e["risk"] == risk]
        return events

    # --- Uptime ---

    def get_uptime(self) -> str:
        """Get System 1 uptime."""
        uptime = datetime.now(timezone.utc) - self._start_time
        return str(uptime)

"""
System 1 Authority Backend Server
- Runs on 127.0.0.1:8101
- Always-on, authoritative, and unstoppable from frontend/System 2.
- Hosts Council, Security, Provider Health, and Audit logic.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from .service import System1Service

# Initialize System 1 Service
system1_service = System1Service()

# FastAPI App for System 1
app = FastAPI(
    title="System 1 Authority",
    version="3.2.0",
    description="Authoritative backend for Agentic-AI. Never stoppable by System 2 or frontend.",
)

# CORS: Allow frontend and System 2 to interact (read-only for them)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5173", "http://localhost:5173", "http://127.0.0.1:8000"],
    allow_methods=["GET", "POST"],  # No DELETE/PUT to modify System 1
    allow_headers=["*"],
)


# --- Models ---
class CouncilVoteRequest(BaseModel):
    """Request to cast a vote in the Council."""
    reviewer: str = Field(..., description="Name of the reviewer (e.g., 'OpenAI', 'Built-in Guard')")
    decision: str = Field(..., description="Vote: ALLOW, DENY, or ESCALATE")
    confidence: float = Field(default=0.8, ge=0.0, le=1.0, description="Confidence score (0-1)")
    reason: str = Field(default="", description="Reason for the vote")


class ProviderConfig(BaseModel):
    """Configuration for a System 1 provider (e.g., OpenAI, Gemini)."""
    name: str = Field(..., description="Provider name")
    enabled: bool = Field(default=True, description="Whether the provider is enabled")
    model: str = Field(default="", description="Default model for this provider")
    timeout: int = Field(default=30, ge=1, le=300, description="Timeout in seconds")
    priority: int = Field(default=1, ge=0, le=10, description="Priority (higher = preferred)")


class AuditEvent(BaseModel):
    """Audit log entry."""
    actor: str = Field(..., description="Who performed the action (e.g., 'System2', 'Frontend')")
    action: str = Field(..., description="Action performed (e.g., 'council_vote', 'tool_execution')")
    run_id: Optional[str] = Field(default=None, description="Associated run ID")
    task_id: Optional[str] = Field(default=None, description="Associated task ID")
    result: str = Field(..., description="Result of the action (e.g., 'ALLOW', 'DENY')")
    risk: str = Field(default="LOW", description="Risk level (SAFE/LOW/MEDIUM/HIGH/CRITICAL)")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


# --- Endpoints ---

@app.get("/api/system1/health")
def system1_health() -> Dict[str, Any]:
    """
    Check System 1 health.
    - Always returns "HEALTHY" if System 1 is running.
    - Includes component statuses (Council, Security, Providers).
    """
    return {
        "status": "HEALTHY",
        "service": "System 1 Authority",
        "version": "3.2.0",
        "uptime": system1_service.get_uptime(),
        "components": {
            "council": system1_service.get_council_status(),
            "security": system1_service.get_security_status(),
            "providers": system1_service.get_provider_status(),
        },
        "authority": True,
        "always_on": True,
        "can_be_stopped": False,  # Explicitly false
    }


@app.get("/api/system1/council")
def get_council_status() -> Dict[str, Any]:
    """
    Get current Council configuration and votes.
    """
    return {
        "mode": system1_service.council_mode,
        "minimum_confidence": system1_service.minimum_confidence,
        "minimum_reviews": system1_service.minimum_reviews,
        "fail_closed_on_disagreement": system1_service.fail_closed_on_disagreement,
        "eligible_reviewers": system1_service.eligible_reviewers,
        "recent_votes": system1_service.get_recent_votes(),
    }


@app.post("/api/system1/council/vote")
def council_vote(request: CouncilVoteRequest) -> Dict[str, Any]:
    """
    Cast a vote in the Council.
    - Only System 1 can call this (frontend/System 2 votes are proxied via System 1).
    - Returns the Council's final decision.
    """
    vote_result = system1_service.cast_vote(
        reviewer=request.reviewer,
        decision=request.decision,
        confidence=request.confidence,
        reason=request.reason,
    )
    return {
        "vote_id": vote_result["vote_id"],
        "decision": vote_result["decision"],
        "allowed": vote_result["allowed"],
        "confidence": vote_result["confidence"],
        "votes": vote_result["votes"],
        "timestamp": vote_result["timestamp"],
    }


@app.get("/api/system1/providers")
def list_providers() -> List[Dict[str, Any]]:
    """
    List all System 1 providers (e.g., OpenAI, Gemini, Anthropic, Built-in Guard).
    """
    return system1_service.list_providers()


@app.get("/api/system1/providers/{provider_name}")
def get_provider_status(provider_name: str) -> Dict[str, Any]:
    """
    Get status of a specific provider.
    """
    provider = system1_service.get_provider(provider_name)
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")
    return provider


@app.post("/api/system1/providers/{provider_name}/enable")
def enable_provider(provider_name: str) -> Dict[str, Any]:
    """
    Enable a provider.
    """
    success = system1_service.enable_provider(provider_name)
    if not success:
        raise HTTPException(status_code=404, detail="Provider not found")
    return {"status": "enabled", "provider": provider_name}


@app.post("/api/system1/providers/{provider_name}/disable")
def disable_provider(provider_name: str) -> Dict[str, Any]:
    """
    Disable a provider.
    """
    success = system1_service.disable_provider(provider_name)
    if not success:
        raise HTTPException(status_code=404, detail="Provider not found")
    return {"status": "disabled", "provider": provider_name}


@app.get("/api/system1/audit")
def list_audit_events(
    limit: int = Query(default=100, ge=1, le=1000),
    actor: Optional[str] = None,
    action: Optional[str] = None,
    risk: Optional[str] = None,
) -> Dict[str, Any]:
    """
    List audit events with filters.
    """
    events = system1_service.list_audit_events(limit=limit, actor=actor, action=action, risk=risk)
    return {"count": len(events), "events": events}


@app.post("/api/system1/audit")
def log_audit_event(event: AuditEvent) -> Dict[str, Any]:
    """
    Log an audit event (called by System 1 internally or via secure hooks).
    """
    event_id = system1_service.log_audit_event(
        actor=event.actor,
        action=event.action,
        run_id=event.run_id,
        task_id=event.task_id,
        result=event.result,
        risk=event.risk,
        metadata=event.metadata,
    )
    return {"event_id": event_id, "status": "logged"}


@app.get("/api/system1/security")
def get_security_rules() -> Dict[str, Any]:
    """
    Get current security rules.
    """
    return {
        "system1_authority": True,
        "system1_always_on": True,
        "system2_authority": False,
        "system2_loopback_only": True,
        "remote_system2_fallback": False,
        "execution_requires_council": True,
        "execution_requires_tool_permission": True,
        "critical_tools_blocked_by_default": True,
        "unknown_actions_fail_closed": True,
    }


# --- Run Server ---
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8101, log_level="info")

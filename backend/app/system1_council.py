from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class CouncilPolicy:
    mode: str = "consensus"
    minimum_confidence: float = 0.50
    minimum_reviews: int = 1
    fail_closed_on_disagreement: bool = True


_ACTION_ALIASES = {
    "allow_guarded_execution": "allow",
    "execute_guarded_plan": "allow",
    "approve": "allow",
    "approved": "allow",
    "deny_execution": "deny",
    "blocked": "deny",
    "reject": "deny",
    "escalate_review": "escalate",
    "review": "escalate",
}


def normalize_action(action: Any) -> str:
    value = str(action or "escalate").strip().lower()
    return _ACTION_ALIASES.get(value, value if value in {"allow", "deny", "escalate"} else "escalate")


def decide(reviews: list[dict[str, Any]], policy: CouncilPolicy) -> dict[str, Any]:
    valid = [r for r in reviews if r.get("status") == "ok"]
    eligible = [r for r in valid if float(r.get("confidence", 0)) >= policy.minimum_confidence]
    if len(eligible) < policy.minimum_reviews:
        return {"decision": "escalate", "allowed": False, "reason": "minimum_reviews_or_confidence_not_met", "eligible_reviews": len(eligible), "disagreement": False, "votes": {"allow": 0.0, "deny": 0.0, "escalate": 0.0}}

    votes = {"allow": 0.0, "deny": 0.0, "escalate": 0.0}
    normalized = []
    for review in eligible:
        action = normalize_action(review.get("action"))
        weight = max(0.01, float(review.get("weight", 1.0)))
        votes[action] += weight
        normalized.append({"model_id": review.get("model_id"), "action": action, "confidence": float(review.get("confidence", 0))})

    ranked = sorted(votes.items(), key=lambda item: item[1], reverse=True)
    winner, winner_weight = ranked[0]
    total = sum(votes.values()) or 1.0
    tied = len(ranked) > 1 and ranked[0][1] == ranked[1][1] and winner_weight > 0
    disagreement = sum(1 for value in votes.values() if value > 0) > 1 or tied

    if policy.mode == "all":
        allowed = all(normalize_action(r.get("action")) == "allow" for r in eligible)
        decision = "allow" if allowed else ("deny" if any(normalize_action(r.get("action")) == "deny" for r in eligible) else "escalate")
    elif policy.mode == "any":
        if any(normalize_action(r.get("action")) == "deny" for r in eligible):
            decision = "deny"
        elif any(normalize_action(r.get("action")) == "allow" for r in eligible):
            decision = "allow"
        else:
            decision = "escalate"
    else:
        decision = "escalate" if tied else winner

    if disagreement and policy.fail_closed_on_disagreement and decision == "allow":
        decision = "escalate"

    return {
        "decision": decision,
        "allowed": decision == "allow",
        "votes": votes,
        "eligible_reviews": len(eligible),
        "disagreement": disagreement,
        "winner_weight": winner_weight,
        "vote_share": winner_weight / total,
        "normalized_reviews": normalized,
        "policy_mode": policy.mode,
    }

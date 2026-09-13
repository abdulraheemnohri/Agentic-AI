from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class CouncilPolicy:
    mode: str = "consensus"
    minimum_confidence: float = 0.50
    minimum_reviews: int = 1
    fail_closed_on_disagreement: bool = True


def decide(reviews: list[dict[str, Any]], policy: CouncilPolicy) -> dict[str, Any]:
    valid = [r for r in reviews if r.get("status") == "ok"]
    eligible = [r for r in valid if float(r.get("confidence", 0)) >= policy.minimum_confidence]
    if len(eligible) < policy.minimum_reviews:
        return {"decision": "escalate", "allowed": False, "reason": "minimum_reviews_or_confidence_not_met", "eligible_reviews": len(eligible), "disagreement": False}

    votes = {"allow": 0.0, "deny": 0.0, "escalate": 0.0}
    for review in eligible:
        action = str(review.get("action", "escalate")).lower()
        if action not in votes:
            action = "escalate"
        weight = max(0.01, float(review.get("weight", 1.0)))
        votes[action] += weight

    ranked = sorted(votes.items(), key=lambda item: item[1], reverse=True)
    winner, winner_weight = ranked[0]
    total = sum(votes.values()) or 1.0
    tied = len(ranked) > 1 and ranked[0][1] == ranked[1][1] and winner_weight > 0
    disagreement = sum(1 for value in votes.values() if value > 0) > 1 or tied

    if policy.mode == "all":
        allowed = all(str(r.get("action", "escalate")).lower() == "allow" for r in eligible)
        decision = "allow" if allowed else ("deny" if any(str(r.get("action", "")).lower() == "deny" for r in eligible) else "escalate")
    elif policy.mode == "any":
        if any(str(r.get("action", "")).lower() == "deny" for r in eligible):
            decision = "deny"
        elif any(str(r.get("action", "")).lower() == "allow" for r in eligible):
            decision = "allow"
        else:
            decision = "escalate"
    else:
        decision = "escalate" if tied else winner

    if disagreement and policy.fail_closed_on_disagreement and decision == "allow":
        decision = "escalate"

    return {"decision": decision, "allowed": decision == "allow", "votes": votes, "eligible_reviews": len(eligible), "disagreement": disagreement, "winner_weight": winner_weight, "vote_share": winner_weight / total}

from __future__ import annotations

from dataclasses import dataclass
from statistics import median
from typing import Any, Callable


@dataclass
class EvaluationResult:
    status: str
    score: float
    confidence: float
    checks: dict[str, bool]
    details: dict[str, Any]

    def as_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "score": self.score,
            "confidence": self.confidence,
            "checks": self.checks,
            "details": self.details,
        }


def deterministic_evaluation(task: dict[str, Any]) -> EvaluationResult:
    steps = task.get("steps", [])
    checks = {
        "task_has_goal": bool(task.get("goal", "").strip()),
        "plan_exists": bool(steps),
        "all_steps_completed": bool(steps) and all(s.get("status") == "completed" for s in steps),
        "verification_passed": bool(task.get("verification", {}).get("passed", False)),
    }
    score = round(sum(checks.values()) / len(checks), 3)
    return EvaluationResult(
        status="passed" if all(checks.values()) else "failed",
        score=score,
        confidence=1.0,
        checks=checks,
        details={"method": "deterministic", "check_count": len(checks)},
    )


def judge_evaluation(task: dict[str, Any], judge: Callable[[dict[str, Any]], dict[str, Any]] | None = None, judge_count: int = 3) -> EvaluationResult:
    if judge is None:
        return EvaluationResult("not_configured", 0.0, 0.0, {}, {"method": "llm_judge", "reason": "No judge model configured in V1."})
    scores = []
    raw = []
    for _ in range(max(1, judge_count)):
        result = judge(task)
        score = max(0.0, min(1.0, float(result.get("score", 0.0))))
        scores.append(score)
        raw.append(result)
    score = round(median(scores), 3)
    confidence = round(1.0 - min(1.0, max(scores) - min(scores)), 3)
    return EvaluationResult("passed" if score >= 0.7 else "failed", score, confidence, {"threshold_met": score >= 0.7}, {"method": "llm_judge", "consensus": "median", "judges": raw})


def human_evaluation(task: dict[str, Any], review: dict[str, Any] | None = None) -> EvaluationResult:
    if review is None:
        return EvaluationResult("not_reviewed", 0.0, 0.0, {}, {"method": "human", "reason": "Awaiting human annotation."})
    score = max(0.0, min(1.0, float(review.get("score", 0.0))))
    return EvaluationResult("passed" if score >= 0.7 else "failed", score, 1.0, {"threshold_met": score >= 0.7}, {"method": "human", "review": review})


def evaluate_task(task: dict[str, Any], judge: Callable[[dict[str, Any]], dict[str, Any]] | None = None, review: dict[str, Any] | None = None) -> dict[str, Any]:
    deterministic = deterministic_evaluation(task)
    llm = judge_evaluation(task, judge)
    human = human_evaluation(task, review)
    active = [r for r in (deterministic, llm, human) if r.status not in {"not_configured", "not_reviewed"}]
    overall = min((r.score for r in active), default=0.0)
    confidence = min((r.confidence for r in active), default=0.0)
    status = "passed" if active and all(r.status == "passed" for r in active) else "failed"
    return {
        "version": "1.6.0",
        "overall_status": status,
        "overall_score": round(overall, 3),
        "confidence": round(confidence, 3),
        "layers": {
            "deterministic": deterministic.as_dict(),
            "llm_judge": llm.as_dict(),
            "human": human.as_dict(),
        },
        "policy": {"aggregation": "minimum_active_layer", "judge_threshold": 0.7, "human_threshold": 0.7},
    }

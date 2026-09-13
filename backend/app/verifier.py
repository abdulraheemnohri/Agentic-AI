from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class VerificationResult:
    passed: bool
    method: str
    message: str
    checks: dict[str, bool]

    def as_dict(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "method": self.method,
            "message": self.message,
            "checks": self.checks,
        }


def verify_step(step: dict[str, Any]) -> VerificationResult:
    method = step.get("verification_method", "output_presence")
    output = step.get("output")
    checks = {
        "completed": step.get("status") == "completed",
        "no_error": not bool(step.get("error")),
    }

    if method == "output_presence":
        checks["output_present"] = output is not None
    elif method == "text_non_empty":
        text = output.get("text") if isinstance(output, dict) else output
        checks["text_non_empty"] = bool(str(text).strip()) if text is not None else False
    elif method == "clock_output":
        checks["clock_present"] = isinstance(output, dict) and bool(output.get("utc"))
    elif method == "none":
        checks = {"completed": step.get("status") == "completed"}
    else:
        checks["known_method"] = False

    passed = all(checks.values())
    return VerificationResult(
        passed=passed,
        method=method,
        message="Verification passed." if passed else "Verification failed: one or more deterministic checks failed.",
        checks=checks,
    )


def verify_task(task: dict[str, Any]) -> dict[str, Any]:
    results = []
    for step in task.get("steps", []):
        results.append({"step_id": step["id"], **verify_step(step).as_dict()})
    passed = bool(results) and all(item["passed"] for item in results)
    return {
        "passed": passed,
        "method": "deterministic_step_verification",
        "message": "All completed steps satisfy their verification criteria." if passed else "One or more steps failed verification.",
        "steps": results,
    }

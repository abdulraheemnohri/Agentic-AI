from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4


@dataclass
class GoldenCase:
    case_id: str
    name: str
    goal: str
    expected_status: str = "passed"
    expected_checks: dict[str, bool] = field(default_factory=dict)
    tags: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "name": self.name,
            "goal": self.goal,
            "expected_status": self.expected_status,
            "expected_checks": self.expected_checks,
            "tags": self.tags,
        }


@dataclass
class RegressionResult:
    run_id: str
    passed: bool
    total: int
    passed_cases: int
    failed_cases: int
    cases: list[dict[str, Any]]

    def as_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "passed": self.passed,
            "total": self.total,
            "passed_cases": self.passed_cases,
            "failed_cases": self.failed_cases,
            "cases": self.cases,
        }


class GoldenDataset:
    def __init__(self) -> None:
        self._cases: dict[str, GoldenCase] = {}
        self.add("basic-success", "Basic successful task", "golden basic success", {"task_has_goal": True, "plan_exists": True, "all_steps_completed": True, "verification_passed": True})

    def add(self, name: str, goal: str, expected_checks: dict[str, bool], expected_status: str = "passed", tags: list[str] | None = None) -> GoldenCase:
        case = GoldenCase(str(uuid4()), name, goal, expected_status, expected_checks, tags or [])
        self._cases[case.case_id] = case
        return case

    def remove(self, case_id: str) -> bool:
        return self._cases.pop(case_id, None) is not None

    def list(self) -> list[dict[str, Any]]:
        return [case.as_dict() for case in self._cases.values()]

    def get(self, case_id: str) -> GoldenCase | None:
        return self._cases.get(case_id)


class RegressionEngine:
    def __init__(self, dataset: GoldenDataset) -> None:
        self.dataset = dataset
        self.history: list[dict[str, Any]] = []

    def run(self, evaluator) -> RegressionResult:
        cases = []
        for case in self.dataset._cases.values():
            task = {"goal": case.goal, "steps": [{"status": "completed"}], "verification": {"passed": True}}
            evaluation = evaluator(task)
            actual = evaluation["layers"]["deterministic"]["checks"]
            checks_match = all(actual.get(k) == v for k, v in case.expected_checks.items())
            status_match = evaluation["overall_status"] == case.expected_status
            passed = checks_match and status_match
            cases.append({"case_id": case.case_id, "name": case.name, "passed": passed, "checks_match": checks_match, "status_match": status_match, "actual_status": evaluation["overall_status"], "actual_score": evaluation["overall_score"]})
        result = RegressionResult(str(uuid4()), bool(cases) and all(c["passed"] for c in cases), len(cases), sum(c["passed"] for c in cases), sum(not c["passed"] for c in cases), cases)
        self.history.append(result.as_dict())
        return result

    def list_history(self) -> list[dict[str, Any]]:
        return list(reversed(self.history))


golden_dataset = GoldenDataset()
regression_engine = RegressionEngine(golden_dataset)

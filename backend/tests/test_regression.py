from app.evaluator import evaluate_task
from app.regression import GoldenDataset, RegressionEngine


def test_golden_case_round_trip():
    dataset = GoldenDataset()
    case = dataset.add("test", "test goal", {"task_has_goal": True})
    assert dataset.get(case.case_id).name == "test"
    assert dataset.remove(case.case_id) is True


def test_regression_passes():
    dataset = GoldenDataset()
    engine = RegressionEngine(dataset)
    result = engine.run(evaluate_task)
    assert result.passed is True
    assert result.failed_cases == 0
    assert len(engine.list_history()) == 1


def test_regression_detects_expected_mismatch():
    dataset = GoldenDataset()
    dataset.add("bad-expectation", "normal goal", {"verification_passed": False}, expected_status="failed")
    engine = RegressionEngine(dataset)
    result = engine.run(evaluate_task)
    assert result.passed is False
    assert result.failed_cases >= 1

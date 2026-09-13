from app.evaluator import deterministic_evaluation, evaluate_task, judge_evaluation


def task():
    return {
        "goal": "hello",
        "steps": [{"status": "completed"}],
        "verification": {"passed": True},
    }


def test_deterministic_passes():
    result = deterministic_evaluation(task())
    assert result.status == "passed"
    assert result.score == 1.0
    assert result.confidence == 1.0


def test_judge_uses_median_consensus():
    values = iter([0.6, 0.9, 0.8])
    result = judge_evaluation(task(), lambda _: {"score": next(values)})
    assert result.score == 0.8
    assert result.status == "passed"


def test_missing_judge_is_explicit():
    result = evaluate_task(task())
    assert result["layers"]["llm_judge"]["status"] == "not_configured"
    assert result["overall_status"] == "passed"

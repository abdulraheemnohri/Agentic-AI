from app.verifier import verify_step, verify_task


def test_output_presence_passes():
    result = verify_step({"id": "s1", "status": "completed", "output": {"text": "ok"}, "verification_method": "output_presence"})
    assert result.passed


def test_empty_text_fails():
    result = verify_step({"id": "s1", "status": "completed", "output": {"text": ""}, "verification_method": "text_non_empty"})
    assert not result.passed


def test_clock_verification():
    result = verify_step({"id": "s1", "status": "completed", "output": {"utc": "now"}, "verification_method": "clock_output"})
    assert result.passed


def test_task_verification_aggregates_steps():
    result = verify_task({"steps": [{"id": "s1", "status": "completed", "output": {"text": "ok"}, "verification_method": "text_non_empty"}]})
    assert result["passed"]

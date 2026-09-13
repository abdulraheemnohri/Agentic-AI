import pytest

from app.planner import Plan, PlanStep, build_default_plan, topological_order, validate_plan


def test_default_plan_is_ordered():
    plan = build_default_plan("test goal")
    assert topological_order(plan) == ["step-1", "step-2", "step-3"]


def test_parallel_steps_are_supported():
    plan = Plan(
        goal="parallel",
        steps=[
            PlanStep(id="a", title="A", tool="echo"),
            PlanStep(id="b", title="B", tool="clock"),
            PlanStep(id="c", title="C", tool="echo", depends_on=["a", "b"]),
        ],
    )
    validate_plan(plan, {"echo", "clock"})
    assert set(topological_order(plan)[:2]) == {"a", "b"}


def test_cycle_is_rejected():
    plan = Plan(
        goal="cycle",
        steps=[
            PlanStep(id="a", title="A", tool="echo", depends_on=["b"]),
            PlanStep(id="b", title="B", tool="clock", depends_on=["a"]),
        ],
    )
    with pytest.raises(ValueError, match="dependency_cycle"):
        validate_plan(plan, {"echo", "clock"})


def test_unknown_tool_is_rejected():
    plan = Plan(goal="bad", steps=[PlanStep(id="a", title="A", tool="missing")])
    with pytest.raises(ValueError, match="unknown_tool"):
        validate_plan(plan, {"echo"})

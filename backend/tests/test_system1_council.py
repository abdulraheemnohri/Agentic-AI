from app.system1_council import CouncilPolicy, decide, normalize_action


def reviews(*actions):
    return [{"status": "ok", "model_id": f"m{i}", "action": action, "confidence": .9} for i, action in enumerate(actions)]


def test_consensus_majority_allows():
    result = decide(reviews("allow", "allow", "deny"), CouncilPolicy("consensus", .5, 1, False))
    assert result["decision"] == "allow"


def test_fail_closed_on_disagreement():
    result = decide(reviews("allow", "deny"), CouncilPolicy("consensus", .5, 1, True))
    assert result["decision"] == "escalate"
    assert result["disagreement"] is True


def test_all_requires_every_review_to_allow():
    result = decide(reviews("allow", "deny"), CouncilPolicy("all", .5, 1, False))
    assert result["allowed"] is False


def test_any_allows_when_one_allows_and_no_deny():
    result = decide(reviews("allow", "escalate"), CouncilPolicy("any", .5, 1, False))
    assert result["decision"] == "allow"


def test_minimum_confidence_escalates():
    result = decide([{"status": "ok", "action": "allow", "confidence": .4}], CouncilPolicy("any", .5, 1, False))
    assert result["decision"] == "escalate"


def test_builtin_guard_alias_is_allow():
    assert normalize_action("allow_guarded_execution") == "allow"
    result = decide(reviews("allow_guarded_execution"), CouncilPolicy("consensus", .5, 1, True))
    assert result["allowed"] is True


def test_unknown_action_fails_closed():
    result = decide(reviews("unknown_model_action"), CouncilPolicy("consensus", .5, 1, True))
    assert result["decision"] == "escalate"
    assert result["allowed"] is False

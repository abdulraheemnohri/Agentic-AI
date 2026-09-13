import asyncio

from app.model_adapter import ModelRequest, get_model, list_models, list_system1_models, register_local_system2, runtime, set_active_model, system1_review


def test_local_model_is_offline():
    response = asyncio.run(get_model().generate(ModelRequest(goal="test")))
    assert response.model_id == "local-deterministic-v2.2"
    assert response.metadata["network"] is False
    assert response.metadata["external_api"] is False


def test_model_registry_and_selection():
    models = list_models()
    assert any(model["model_id"] == "local-deterministic-v2.2" for model in models)
    status = set_active_model("local-deterministic-v2.2")
    assert status["active_system2"] == runtime.active_system2


def test_system1_has_builtin_and_external_provider_slots():
    providers = {item["model_id"] for item in list_system1_models()}
    assert "system1-local-guard" in providers
    assert "system1-openai" in providers
    assert "system1-gemini" in providers
    assert "system1-anthropic" in providers


def test_builtin_system1_review_works_without_api_keys():
    result = asyncio.run(system1_review(ModelRequest(goal="test", available_tools=[{"name":"echo","risk":"SAFE","policy":"AUTO"}], constraints={})))
    assert result["allowed"] is True
    assert any(item["model_id"] == "system1-local-guard" and item["status"] == "ok" for item in result["reviews"])


def test_system2_local_server_requires_loopback():
    try:
        register_local_system2("bad", "https://example.com", "model")
        assert False
    except ValueError as exc:
        assert "loopback" in str(exc)

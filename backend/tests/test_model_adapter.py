import asyncio

from app.model_adapter import ModelRequest, get_model, list_models, runtime, set_active_model


def test_local_model_is_offline():
    response = asyncio.run(get_model().generate(ModelRequest(goal="test")))
    assert response.model_id == "local-deterministic-v2.1"
    assert response.metadata["network"] is False
    assert response.metadata["external_api"] is False


def test_model_registry_and_selection():
    models = list_models()
    assert any(model["model_id"] == "local-deterministic-v2.1" for model in models)
    status = set_active_model("local-deterministic-v2.1")
    assert status["active_model"] == runtime.active_model

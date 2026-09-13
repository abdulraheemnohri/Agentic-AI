from pathlib import Path

import app.model_manager as mm


def test_local_registry_rejects_non_loopback(tmp_path, monkeypatch):
    monkeypatch.setattr(mm, "CONFIG_PATH", tmp_path / "registry.json")
    try:
        mm.register_system2("remote", "test", "https://example.com", "model")
        assert False, "remote System 2 endpoint must be rejected"
    except ValueError as exc:
        assert str(exc) == "system2_local_only:base_url_must_be_loopback"


def test_policy_is_persistent(tmp_path, monkeypatch):
    monkeypatch.setattr(mm, "CONFIG_PATH", tmp_path / "registry.json")
    policy = mm.set_system1_policy("all", 0.75, 2)
    assert policy["mode"] == "all"
    assert mm.get_system1_policy()["minimum_confidence"] == 0.75
    assert Path(mm.CONFIG_PATH).exists()

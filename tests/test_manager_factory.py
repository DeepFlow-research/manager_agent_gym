import pytest

from manager_agent_gym.core.manager_agent.factory import (
    create_manager_agent,
    manager_mode_label,
)
from manager_agent_gym.core.manager_agent.structured_manager import (
    ChainOfThoughtManagerAgent,
)
from manager_agent_gym.core.manager_agent.random_manager import (
    RandomManagerAgentV2,
    OneShotDelegateManagerAgent,
)
from manager_agent_gym.schemas.preferences.preference import PreferenceWeights


def _prefs():
    return PreferenceWeights(preferences=[])


def _clear_env(monkeypatch) -> None:
    for k in ["MAG_MANAGER_MODE", "MAG_MODEL_NAME"]:
        monkeypatch.delenv(k, raising=False)


def test_default_mode_is_cot_and_model_default(monkeypatch) -> None:
    _clear_env(monkeypatch)
    mgr = create_manager_agent(preferences=_prefs())
    assert isinstance(mgr, ChainOfThoughtManagerAgent)


@pytest.mark.parametrize(
    "alias,expected",
    [
        ("cot", ChainOfThoughtManagerAgent),
        ("random", RandomManagerAgentV2),
        ("assign_all", OneShotDelegateManagerAgent),
    ],
)
def test_mode_aliases_map_correctly(monkeypatch, alias, expected) -> None:
    _clear_env(monkeypatch)
    mgr = create_manager_agent(preferences=_prefs(), manager_mode=alias)
    assert isinstance(mgr, expected)


def test_env_overrides(monkeypatch) -> None:
    monkeypatch.setenv("MAG_MANAGER_MODE", "random")
    monkeypatch.setenv("MAG_MODEL_NAME", "o4-mini")
    mgr = create_manager_agent(preferences=_prefs())
    assert isinstance(mgr, RandomManagerAgentV2)


def test_invalid_mode_raises(monkeypatch) -> None:
    monkeypatch.setenv("MAG_MANAGER_MODE", "invalid_mode")
    with pytest.raises(ValueError):
        _ = manager_mode_label()


def test_manager_mode_label_reflects_env(monkeypatch) -> None:
    monkeypatch.setenv("MAG_MANAGER_MODE", "assign_all")
    assert manager_mode_label() == "assign_all"

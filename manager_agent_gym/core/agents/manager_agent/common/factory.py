from __future__ import annotations

import os
from typing import Callable, Dict, TYPE_CHECKING

if TYPE_CHECKING:
    from manager_agent_gym.core.common.llm_generator import LLMGenerator

from manager_agent_gym.core.agents.manager_agent.common.interface import ManagerAgent
from manager_agent_gym.core.agents.manager_agent.implementations.chain_of_thought import (
    ChainOfThoughtManagerAgent,
)
from manager_agent_gym.core.agents.manager_agent.implementations.random_manager import (
    RandomManagerAgentV2,
)
from manager_agent_gym.core.agents.manager_agent.implementations.one_shot_delegation import (
    OneShotDelegateManagerAgent,
)
from manager_agent_gym.core.agents.manager_agent.implementations.noop_manager import (
    NoOpManagerAgent,
)
from manager_agent_gym.schemas.preferences.preference import PreferenceSnapshot


def _normalize_mode(raw_mode: str | None) -> str:
    if not raw_mode:
        return "cot"
    mode = raw_mode.strip().lower()
    allowed = {"cot", "random", "assign_all", "noop"}
    if mode not in allowed:
        raise ValueError(
            f"Unsupported MAG_MANAGER_MODE='{raw_mode}'. Use one of: cot, random, assign_all, noop"
        )
    return mode


def _resolve_model_name(explicit_model_name: str | None) -> str:
    if explicit_model_name:
        return explicit_model_name
    return os.environ.get("MAG_MODEL_NAME", "o3")


def create_manager_agent(
    llm_generator: "LLMGenerator",  # REQUIRED - must be passed explicitly
    preferences: PreferenceSnapshot,
    model_name: str | None = None,
    manager_mode: str | None = None,
) -> ManagerAgent:
    """Create a manager agent instance based on mode and model settings.

    Args:
        llm_generator: LLM generator (shared across workflow for training)
        preferences: Preference weights used by the manager agent.
        model_name: Optional model identifier (defaults from MAG_MODEL_NAME or "o3").
        manager_mode: Optional explicit mode (defaults from MAG_MANAGER_MODE or "cot").

    Returns:
        An initialized ManagerAgent implementation.
    """

    resolved_mode = _normalize_mode(
        manager_mode or os.environ.get("MAG_MANAGER_MODE", "cot")
    )
    resolved_model = _resolve_model_name(model_name)

    creators: Dict[str, Callable[[], ManagerAgent]] = {
        "cot": lambda: ChainOfThoughtManagerAgent(
            llm_generator=llm_generator,
            preferences=preferences,
            model_name=resolved_model,
        ),
        # Canonical "random" uses RandomManagerAgentV2 by default
        # Note: RandomManagerAgent doesn't use LLM, but accepts it for consistency
        "random": lambda: RandomManagerAgentV2(
            preferences=preferences, 
            llm_generator=llm_generator,
            model_name=resolved_model, 
            seed=0
        ),
        "assign_all": lambda: OneShotDelegateManagerAgent(
            preferences=preferences,
            llm_generator=llm_generator,
            model_name=resolved_model,
        ),
        "noop": lambda: NoOpManagerAgent(
            agent_id="noop_manager", preferences=preferences
        ),
    }

    if resolved_mode not in creators:
        raise ValueError(
            f"Unknown MAG_MANAGER_MODE='{resolved_mode}'. Supported: cot, random, assign_all, noop"
        )

    return creators[resolved_mode]()


def manager_mode_label(manager_mode: str | None = None) -> str:
    """Return a concise, stable label for the manager mode for use in filepaths."""
    normalized = _normalize_mode(
        manager_mode or os.environ.get("MAG_MANAGER_MODE", "cot")
    )
    return normalized


def create_manager(
    llm_generator: "LLMGenerator",  # REQUIRED - must be passed explicitly
    preferences: PreferenceSnapshot,
    model_name: str | None = None,
    manager_mode: str | None = None,
) -> ManagerAgent:
    """Convenience alias to match example naming; forwards to create_manager_agent."""
    return create_manager_agent(
        llm_generator=llm_generator,
        preferences=preferences,
        model_name=model_name,
        manager_mode=manager_mode,
    )

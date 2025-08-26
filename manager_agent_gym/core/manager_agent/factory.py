"""
Factory helpers to select and construct a ManagerAgent consistently across examples.

Selection is controlled by:
- Explicit function arguments, or
- Environment variables (MAG_MANAGER_MODE, MAG_MODEL_NAME)

Supported manager modes (case-insensitive):
- "cot" → ChainOfThoughtManagerAgent (structured manager)
- "random" or "random_v2" → RandomManagerAgentV2
- "random_v1" → RandomManagerAgent
- "oneshot" → OneShotDelegateManagerAgent
"""

from __future__ import annotations

import os
from typing import Callable, Dict

from .interface import ManagerAgent
from .structured_manager import ChainOfThoughtManagerAgent
from .random_manager import (
    RandomManagerAgentV2,
    OneShotDelegateManagerAgent,
)
from ...schemas.preferences.preference import PreferenceWeights


def _normalize_mode(raw_mode: str | None) -> str:
    if not raw_mode:
        return "cot"
    mode = raw_mode.strip().lower()
    allowed = {"cot", "random", "assign_all"}
    if mode not in allowed:
        raise ValueError(
            f"Unsupported MAG_MANAGER_MODE='{raw_mode}'. Use one of: cot, random, assign_all"
        )
    return mode


def _resolve_model_name(explicit_model_name: str | None) -> str:
    if explicit_model_name:
        return explicit_model_name
    return os.environ.get("MAG_MODEL_NAME", "o3")


def create_manager_agent(
    preferences: PreferenceWeights,
    model_name: str | None = None,
    manager_mode: str | None = None,
) -> ManagerAgent:
    """Create a manager agent instance based on mode and model settings.

    Args:
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
            preferences=preferences, model_name=resolved_model
        ),
        # Canonical "random" uses RandomManagerAgentV2 by default
        "random": lambda: RandomManagerAgentV2(
            preferences=preferences, model_name=resolved_model, seed=0
        ),
        "assign_all": lambda: OneShotDelegateManagerAgent(preferences=preferences),
    }

    if resolved_mode not in creators:
        raise ValueError(
            f"Unknown MAG_MANAGER_MODE='{resolved_mode}'. Supported: cot, random, assign_all"
        )

    return creators[resolved_mode]()


def manager_mode_label(manager_mode: str | None = None) -> str:
    """Return a concise, stable label for the manager mode for use in filepaths."""
    normalized = _normalize_mode(
        manager_mode or os.environ.get("MAG_MANAGER_MODE", "cot")
    )
    return normalized


def create_manager(
    preferences: PreferenceWeights,
    model_name: str | None = None,
    manager_mode: str | None = None,
) -> ManagerAgent:
    """Convenience alias to match example naming; forwards to create_manager_agent."""
    return create_manager_agent(
        preferences=preferences, model_name=model_name, manager_mode=manager_mode
    )

"""
Stakeholder configuration and public profile schemas.

These models define the minimal public exposure and persona configuration for
the simulated stakeholder. The stakeholder's dynamic preference state remains
private to the simulator and is not exposed via these schemas.
"""

from pydantic import BaseModel, Field
from .config import AgentConfig
from ..preferences.preference import PreferenceWeights
from ..preferences.preference import PreferenceChange


class StakeholderPublicProfile(BaseModel):
    """Minimal public information about the stakeholder available to the manager."""

    display_name: str = Field(..., description="Stakeholder display name")
    role: str = Field(..., description="Stakeholder role/title")
    preference_summary: str = Field(
        default="",
        description="High-level description of stakeholder priorities.",
    )


class StakeholderConfig(AgentConfig):
    """Configuration for the stakeholder agent persona and messaging behavior.

    Inherits from AgentConfig to align with AgentInterface typing and provide
    standard fields like model_name and system_prompt.
    """

    agent_type: str = Field(default="stakeholder", description="Type identifier")

    # Persona
    name: str = Field(..., description="Stakeholder name")
    role: str = Field(..., description="Stakeholder role/title")
    persona_description: str = Field(
        default="Stakeholder persona",
        description="Short persona description for messaging style",
    )
    model_name: str = Field(
        description="Model name to use for stakeholder agent", default="o3"
    )
    initial_preferences: PreferenceWeights = Field(
        description="Initial, normalized preference weights owned by the stakeholder"
    )

    # Messaging behavior
    response_latency_steps_min: int = Field(
        default=0, ge=0, description="Minimum reply latency in timesteps"
    )
    response_latency_steps_max: int = Field(
        default=2, ge=0, description="Maximum reply latency in timesteps"
    )
    push_probability_per_timestep: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Chance to proactively push a suggestion",
    )
    suggestion_rate: float = Field(
        default=0.25,
        ge=0.0,
        le=1.0,
        description="How often suggestions are created when pushing",
    )
    clarification_reply_rate: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Probability of replying to a clarification message",
    )

    # Review/approval behavior
    strictness: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Higher is stricter when reviewing work",
    )
    verbosity: int = Field(
        default=1,
        ge=0,
        le=5,
        description="Verbosity of stakeholder messages (affects comm cost)",
    )


class StakeholderPreferenceState(BaseModel):
    """Stakeholder-owned preference state for a given timestep."""

    weights: PreferenceWeights = Field(..., description="Preference weights")
    timestep: int = Field(..., description="Timestep for which weights apply")
    change_event: PreferenceChange | None = Field(
        default=None, description="Optional change event metadata"
    )

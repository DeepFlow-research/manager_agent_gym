"""
Common stakeholder personas and helpers for end-to-end examples.
"""

from manager_agent_gym.schemas.preferences.preference import PreferenceSnapshot
from manager_agent_gym.schemas.agents.stakeholder import StakeholderConfig
from manager_agent_gym.core.agents.stakeholder_agent.stakeholder_agent import (
    StakeholderAgent,
)


def _build_persona_config(
    persona: str, preferences: PreferenceSnapshot
) -> StakeholderConfig:
    persona_lower = persona.lower().strip()

    if persona_lower == "nitpicky":
        return StakeholderConfig(
            agent_id="stakeholder_nitpicky",
            agent_type="stakeholder",
            name="Nitpicky Stakeholder",
            role="Detail-Oriented Approver",
            persona_description=(
                "Highly involved, interrupts often, requests clarifications and pushes suggestions."
            ),
            # system_prompt removed - built from template
            model_name="o3",
            preference_data=preferences,
            response_latency_steps_min=0,
            response_latency_steps_max=1,
            push_probability_per_timestep=0.5,
            suggestion_rate=0.7,
            clarification_reply_rate=1.0,
            strictness=0.8,
            verbosity=3,
            agent_description="Nitpicky Stakeholder Agent",
            agent_capabilities=[
                "Approves tasks",
                "Requests clarifications",
                "Pushes suggestions",
            ],
        )

    if persona_lower == "hands_off":
        return StakeholderConfig(
            agent_id="stakeholder_hands_off",
            agent_type="stakeholder",
            name="Hands-Off Stakeholder",
            role="Executive Sponsor",
            persona_description=(
                "Very hands-off, rarely interrupts, minimal clarifications, relies on manager."
            ),
            # system_prompt removed - built from template
            model_name="o3",
            preference_data=preferences,
            response_latency_steps_min=1,
            response_latency_steps_max=3,
            push_probability_per_timestep=0.0,
            suggestion_rate=0.1,
            clarification_reply_rate=0.3,
            strictness=0.4,
            verbosity=1,
            agent_description="Hands-Off Stakeholder Agent",
            agent_capabilities=[
                "Approves tasks",
                "Requests clarifications",
                "Pushes suggestions",
            ],
        )

    # Default to balanced
    return StakeholderConfig(
        agent_id="stakeholder_balanced",
        agent_type="stakeholder",
        name="Balanced Stakeholder",
        role="Business Owner",
        persona_description=(
            "Balanced involvement: occasional clarifications and suggestions; pragmatic and time-aware."
        ),
        # system_prompt removed - built from template
        model_name="o3",
        preference_data=preferences,
        response_latency_steps_min=0,
        response_latency_steps_max=2,
        push_probability_per_timestep=0.1,
        suggestion_rate=0.25,
        clarification_reply_rate=0.8,
        strictness=0.6,
        verbosity=2,
        agent_description="Balanced Stakeholder Agent",
        agent_capabilities=[
            "Approves tasks",
            "Requests clarifications",
            "Pushes suggestions",
        ],
    )


def create_stakeholder_agent(
    persona: str,
    preferences: PreferenceSnapshot,
) -> StakeholderAgent:
    cfg = _build_persona_config(persona, preferences)
    return StakeholderAgent(config=cfg)

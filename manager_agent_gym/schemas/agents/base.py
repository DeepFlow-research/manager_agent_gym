"""
Agent configuration data models.
"""

from typing import Literal

from pydantic import BaseModel, Field, field_validator


class AgentConfig(BaseModel):
    """Base configuration for an agent instance."""

    # Essential identification
    agent_id: str = Field(..., description="Unique identifier for the agent")
    agent_type: str = Field(..., description="Type of agent (ai, human_mock)")

    # Core behavior configuration
    system_prompt: str | None = Field(
        ..., description="System instructions for the agent"
    )
    model_name: str = Field(default="gpt-4.1", description="LLM model to use")

    agent_description: str = Field(..., description="Description of the agent")
    agent_capabilities: list[str] = Field(..., description="Capabilities of the agent")

    # Multimodal configuration
    use_multimodal_resources: bool = Field(
        default=True,
        description="Whether to pass full multimodal resource content to agent",
    )
    max_resource_tokens: int | None = Field(
        default=100000, description="Max tokens for resource content (None = unlimited)"
    )
    image_detail: Literal["auto", "low", "high"] = Field(
        default="high",
        description="Detail level for image analysis (high=detailed, low=faster/cheaper)",
    )

    # Execution configuration
    max_turns: int = Field(
        default=15,
        description="Maximum number of conversation turns for agent execution",
    )
    enable_execution_tracing: bool = Field(
        default=True,
        description="If True, stores detailed execution traces (all LLM calls, tool uses, tokens) for debugging",
    )

    def get_agent_capability_summary(self) -> str:
        """Print a summary of the agent's configuration."""
        return f"Agent {self.agent_id} [{self.agent_type}] | Description: {self.agent_description} | Capabilities: {self.agent_capabilities}"

    @field_validator("agent_id")
    @classmethod
    def validate_agent_id(cls, v: str) -> str:
        """Validate agent_id is not empty and follows naming conventions."""
        if not v or not v.strip():
            raise ValueError("agent_id cannot be empty")
        return v.strip()

    @field_validator("system_prompt")
    @classmethod
    def validate_system_prompt(cls, v: str | None) -> str | None:
        """Validate system_prompt is not empty (if provided)."""
        if v is None:
            return None
        if not v.strip():
            raise ValueError("system_prompt cannot be empty string (use None instead)")
        if len(v) < 10:
            raise ValueError("system_prompt must be at least 10 characters")
        return v.strip()


class AIAgentConfig(AgentConfig):
    """Configuration specific to AI agents.

    Note: For AI agents, system_prompt should be set to None (or a brief specialization).
    The full system prompt is built from a template + agent_description.
    Do not override with custom system prompts as this bypasses execution guidelines.
    """

    agent_type: str = Field(default="ai", description="Type of agent")
    system_prompt: str | None = Field(
        default=None,
        description="DEPRECATED: Use agent_description instead. If set, overrides the standard prompt template (not recommended).",
    )


class HumanAgentConfig(AgentConfig):
    """Unified configuration for human mock agents - includes both technical and persona aspects."""

    agent_type: str = Field(default="human_mock", description="Type of agent")

    # Identity & Persona (formerly HumanPersonaConfig)
    name: str = Field(..., description="Human worker name")
    role: str = Field(..., description="Job title/role")
    experience_years: int = Field(..., ge=0, description="Years of experience")
    expertise_areas: list[str] = Field(
        default_factory=list, description="Areas of expertise"
    )
    personality_traits: list[str] = Field(
        default_factory=list, description="Personality characteristics"
    )
    work_style: str = Field(
        default="methodical",
        description="Working style (methodical, creative, fast, etc.)",
    )
    background: str = Field(..., description="Professional background and context")

    # Operational Parameters
    base_work_hours: float = Field(
        default=8.0, ge=1.0, le=16.0, description="Daily work hours for this human"
    )
    hourly_rate: float = Field(
        default=50.0,
        description="Hourly rate for cost calculation",
    )
    interruption_tolerance: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="How well this human handles interruptions",
    )

    # Simulation Parameters (formerly NoiseConfig - simplified)
    base_quality_mean: float = Field(
        default=0.85,
        ge=0.0,
        le=1.0,
        description="Base quality level [0-1]",
    )
    fatigue_rate: float = Field(
        default=0.02,
        ge=0.0,
        description="Quality degradation per hour worked",
    )
    misunderstanding_rate: float = Field(
        default=0.05,
        ge=0.0,
        le=1.0,
        description="Chance of task misunderstanding",
    )

    @property
    def experience_factor(self) -> float:
        """Auto-calculate experience factor from years."""
        return min(0.5 + (self.experience_years * 0.1), 3.0)

    @field_validator("hourly_rate")
    @classmethod
    def validate_hourly_rate(cls, v: float) -> float:
        """Validate hourly_rate is positive."""
        if v <= 0:
            raise ValueError("hourly_rate must be positive")
        return v

    def generate_roleplay_prompt(self) -> str:
        """Generate a roleplay prompt for the AI to embody this persona."""
        # Lazy import to avoid circular dependency
        from manager_agent_gym.core.agents.workflow_agents.prompts.persona_prompts_from_schemas import (
            PERSONA_ROLEPLAY_TEMPLATE,
        )

        expertise_str = (
            ", ".join(self.expertise_areas)
            if self.expertise_areas
            else "general business"
        )
        traits_str = (
            ", ".join(self.personality_traits)
            if self.personality_traits
            else "professional"
        )

        return PERSONA_ROLEPLAY_TEMPLATE.format(
            name=self.name,
            role=self.role,
            experience_years=self.experience_years,
            background=self.background,
            expertise=expertise_str,
            personality=traits_str,
            work_style=self.work_style,
        )

"""
Agent output data models for different agent types.
"""

from pydantic import BaseModel, Field
from manager_agent_gym.schemas.domain.resource import Resource


class AITaskOutput(BaseModel):
    """
    Structured output representing the result of an AI task execution.

    It should have the reasoning be the reasoning as to what the resources be, and ALWAYS have at least one resource.
    """

    reasoning: str = Field(
        ..., description="Your thought process and key decisions about this task"
    )
    resources: list[Resource] = Field(
        ...,
        description="Resources created by the AI agent. There MUST BE AT LEAST ONE RESOURCE.",
    )
    confidence: float = Field(
        default=0.8,
        ge=0.0,
        le=1.0,
        description="Your confidence in the result quality (0.0-1.0). Defaults to 0.8 if not specified.",
    )
    execution_notes: list[str] = Field(
        default_factory=list,
        description="Any important observations, challenges, or considerations during execution",
    )


class HumanWorkOutput(BaseModel):
    """Structured output format for human work simulation."""

    reasoning: str = Field(
        ..., description="Your thought process and approach to this task"
    )
    resources: list[Resource] = Field(
        ...,
        description="Resources created by the human agent. There MUST BE AT LEAST ONE RESOURCE.",
    )
    work_process: str = Field(
        default="Standard workflow process applied",
        description="Description of how the work was completed",
    )
    challenges_encountered: list[str] = Field(
        default_factory=list,
        description="Any challenges or obstacles faced during execution",
    )
    quality_notes: str = Field(
        default="Work completed to specification",
        description="Notes about work quality and attention to detail",
    )
    confidence_level: str = Field(
        default="high", description="Confidence in the work quality (low/medium/high)"
    )


class HumanTimeEstimation(BaseModel):
    """Structured output format for human time estimation."""

    reasoning: str
    estimated_hours: float

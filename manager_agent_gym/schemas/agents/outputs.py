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

    reasoning: str
    resources: list[Resource] = Field(
        description="Resources created by the AI agent. There MUST BE AT LEAST ONE RESOURCE."
    )
    confidence: float
    execution_notes: list[str]


class HumanWorkOutput(BaseModel):
    """Structured output format for human work simulation."""

    reasoning: str
    resources: list[Resource] = Field(
        description="Resources created by the human agent. There MUST BE AT LEAST ONE RESOURCE."
    )
    work_process: str
    challenges_encountered: list[str]
    quality_notes: str
    confidence_level: str


class HumanTimeEstimation(BaseModel):
    """Structured output format for human time estimation."""

    reasoning: str
    estimated_hours: float

"""
Agent output data models for different agent types.
"""

from pydantic import BaseModel
from ...schemas.core.resources import Resource


class AITaskOutput(BaseModel):
    """Structured output format for AI task execution."""

    resources: list[Resource]
    reasoning: str
    confidence: float
    execution_notes: list[str]


class HumanWorkOutput(BaseModel):
    """Structured output format for human work simulation."""

    resources: list[Resource]
    work_process: str
    challenges_encountered: list[str]
    quality_notes: str
    confidence_level: str


class HumanTimeEstimation(BaseModel):
    """Structured output format for human time estimation."""

    reasoning: str
    estimated_hours: float

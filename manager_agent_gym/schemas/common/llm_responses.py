"""
Common LLM response schemas.
"""

from pydantic import BaseModel, Field
from enum import Enum

from ...schemas.core.tasks import SubtaskData


class LLMScoreLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class LLMScoredResponse(BaseModel):
    """Response structure for LLM numeric scoring."""

    reasoning: str = Field(
        ..., description="Explanation of the assessment and rationale for the score"
    )
    score: float | LLMScoreLevel | bool = Field(
        ..., description="Numeric score assigned by LLM"
    )


class SubtaskResponse(BaseModel):
    """Response schema for LLM-generated subtasks."""

    reasoning: str = Field(..., description="Explanation of the decomposition approach")
    subtasks: list[SubtaskData] = Field(
        ..., description="List of structured subtask data"
    )

"""
Preference Dynamics Schema Types.

Types for non-stationary preference changes during workflow execution.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class PreferenceChangeEvent(BaseModel):
    """
    A preference change event in the workflow.

    Records when and how preferences changed during execution.
    """

    event_id: str = Field(..., description="Unique identifier for this change event")
    workflow_id: UUID = Field(..., description="ID of the affected workflow")
    timestamp: datetime = Field(..., description="When the change occurred")

    # Change details
    previous_weights: list[float] = Field(
        ..., description="Preference weights before change"
    )
    new_weights: list[float] = Field(..., description="Preference weights after change")
    preference_names: list[str] = Field(
        ..., description="Names of preference dimensions"
    )

    # Change metadata
    change_type: str = Field(
        ..., description="Type of change (drift, shock, rebalance)"
    )
    magnitude: float = Field(..., description="Magnitude of the change [0,1]")
    trigger_reason: str = Field(..., description="Human-readable reason for change")

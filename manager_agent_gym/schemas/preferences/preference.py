from typing import List
from pydantic import BaseModel, Field, model_validator  # type: ignore

from manager_agent_gym.schemas.preferences.evaluator import Rubric


class Preference(BaseModel):
    """
    A single preference dimension with its weight and associated rubric.
    """

    name: str = Field(..., description="Name of the preference dimension")
    weight: float = Field(
        ge=0.0, le=1.0, description="Weight/importance of this preference [0,1]"
    )
    description: str | None = Field(
        default=None,
        description="Optional description of what this preference measures",
    )
    evaluator: Rubric | None = Field(
        default=None,
        description="Rubric defining criteria and aggregation for this preference",
    )

    def get_rubric_names(self) -> List[str]:
        """Get names of all criteria in this preference's rubric."""
        if self.evaluator is None:
            return []
        return [criterion.name for criterion in self.evaluator.criteria]


class PreferenceSnapshot(BaseModel):
    """
    A collection of multi-objective preference weights for workflow optimization.
    Weights are automatically normalized to sum to 1.0 upon initialization.
    """

    preferences: List[Preference] = Field(
        default_factory=list, description="List of preference dimensions"
    )
    timestep: int = Field(
        default=0, description="Timestep at which these preferences apply"
    )

    @model_validator(mode="after")
    def normalize_weights(self) -> "PreferenceSnapshot":
        total_weight = sum(p.weight for p in self.preferences)
        if total_weight > 0:
            for p in self.preferences:
                p.weight = p.weight / total_weight
        elif self.preferences:
            equal_weight = 1.0 / len(self.preferences)
            for p in self.preferences:
                p.weight = equal_weight
        return self

    def get_preference_names(self) -> List[str]:
        """Get all preference dimension names."""
        return [pref.name for pref in self.preferences]

    def get_preference_dict(self) -> dict[str, float]:
        """Get preferences as a dictionary mapping name to normalized weight."""
        return {pref.name: pref.weight for pref in self.preferences}

    def normalize(self) -> "PreferenceSnapshot":
        """Return a new PreferenceWeights with normalized weights."""
        return PreferenceSnapshot(
            preferences=[p.model_copy() for p in self.preferences]
        )

    def get_preference_summary(self) -> str:
        """Get a summary of the preferences."""
        return "\n".join([f"{pref.name}: {pref.weight}" for pref in self.preferences])


class PreferenceChangeEvent(BaseModel):
    """
    Minimal event representing a change of preferences at a specific timestep.
    """

    timestep: int = Field(..., ge=0, description="Timestep at which the change occurs")
    preferences: PreferenceSnapshot = Field(
        ..., description="The full set of preferences active after the change"
    )
    # Optional metadata for UI/logging/back-compat with earlier usage
    change_type: str | None = Field(default=None, description="Type of change event")
    magnitude: float | None = Field(
        default=None, description="Magnitude of change if applicable"
    )
    trigger_reason: str | None = Field(
        default=None, description="Reason the change was triggered"
    )
    previous_weights: dict[str, float] | None = Field(
        default=None, description="Previous normalized weights by preference name"
    )
    new_weights: dict[str, float] | None = Field(
        default=None, description="New normalized weights by preference name"
    )

from typing import Literal
from pydantic import BaseModel, Field


# Modes for interpreting the provided changes
WeightUpdateMode = Literal["delta", "multiplier", "absolute"]

# What to do when a change references a preference name that doesn't exist
MissingPreferencePolicy = Literal["error", "ignore", "create_zero"]

# How to redistribute remaining mass for unspecified names in absolute mode
RedistributionStrategy = Literal["proportional", "uniform"]


class PreferenceWeightUpdateRequest(BaseModel):
    """
    Request to update a stakeholder's preference weights at a given timestep.

    - mode="delta": add deltas to existing weights for the specified names
    - mode="multiplier": multiply existing weights by given factors
    - mode="absolute": set specified names to exact weights; optionally
      redistribute the remainder across unspecified names
    """

    timestep: int = Field(..., ge=0, description="Timestep when the update applies")
    changes: dict[str, float] = Field(
        default_factory=dict,
        description="Mapping from preference name to change value (delta/factor/absolute)",
    )
    mode: WeightUpdateMode = Field(default="delta")
    normalize: bool = Field(
        default=True, description="Normalize resulting weights to sum to 1.0"
    )
    clamp_zero: bool = Field(
        default=True, description="Clamp any negative weights to zero after update"
    )
    missing: MissingPreferencePolicy = Field(
        default="error",
        description="Policy for unknown preference names in 'changes'",
    )
    redistribution: RedistributionStrategy = Field(
        default="proportional",
        description="Redistribution strategy for unspecified names when mode='absolute'",
    )

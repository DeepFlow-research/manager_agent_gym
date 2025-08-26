from pydantic import BaseModel, Field
from uuid import UUID, uuid4
from typing import Any


class Constraint(BaseModel):
    """
    A regulatory or organizational constraint on workflow execution.

    Supports governance and compliance requirements.
    """

    constraint_id: UUID = Field(default_factory=uuid4)
    name: str = Field(..., description="Name of the constraint")
    description: str = Field(..., description="Detailed description of the constraint")
    constraint_type: str = Field(
        ..., description="Type: 'hard', 'soft', 'regulatory', 'organizational'"
    )
    enforcement_level: float = Field(
        ge=0.0, le=1.0, description="How strictly to enforce [0,1]"
    )
    applicable_task_types: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

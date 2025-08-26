"""
Dynamic action schema constraints for manager agents.

Builds per-timestep constrained Pydantic schemas that restrict ID fields
to the set of valid values observed in the workflow at that timestep.
"""

from __future__ import annotations

from typing import Any, Type, Union, cast

from pydantic import BaseModel, Field, create_model

from ...schemas.execution.manager_actions import BaseManagerAction
from ...schemas.execution.manager import ManagerObservation


def build_context_constrained_action_schema(
    action_classes: list[type[BaseManagerAction]], observation: ManagerObservation
) -> Type[BaseModel]:
    """
    Build a Pydantic model to use as response_format that constrains action parameters
    (e.g., task_id, agent_id) to only valid values from the current observation.
    """

    constrained_union: Any
    if len(action_classes) == 1:
        constrained_union = action_classes[
            0
        ]  # _constrain_action_class(action_classes[0], observation)
    else:
        constrained_union = Union[
            tuple(
                ac for ac in action_classes
            )  # _constrain_action_class(ac, observation) for ac in action_classes)
        ]

    class ConstrainedManagerAction(BaseModel):
        reasoning: str = Field(
            description="Your reasoning for choosing this action to advance the workflow"
        )
        action: constrained_union = Field(  # type: ignore
            description="The specific action to take"
        )

    return ConstrainedManagerAction


def _constrain_action_class(
    action_class: type[BaseManagerAction], observation: ManagerObservation
) -> type[BaseManagerAction]:
    """
    Create a new action class with ID fields replaced by dynamic Enums of allowed values.
    """
    fields_any: dict[str, tuple[Any, Any]] = {}

    for name, info in action_class.model_fields.items():  # type: ignore[attr-defined]
        annotation = info.annotation

        # Map known ID fields to allowed sets via JSON Schema enum hints while preserving runtime types
        if name in {"task_id", "prerequisite_task_id", "dependent_task_id"}:
            allowed = [str(x) for x in observation.task_ids]
            fields_any[name] = (
                annotation if annotation is not None else str,
                Field(
                    description=info.description,
                    default=info.default,
                    json_schema_extra={"enum": cast(list[Any], allowed)},
                ),
            )
        elif name == "agent_id":
            allowed = [str(x) for x in observation.agent_ids]
            fields_any[name] = (
                annotation if annotation is not None else str,
                Field(
                    description=info.description,
                    default=info.default,
                    json_schema_extra={"enum": cast(list[Any], allowed)},
                ),
            )
        elif name == "receiver_id":
            allowed = [str(x) for x in observation.agent_ids]
            enum_with_null = cast(list[Any], allowed + [None])
            underlying = annotation if annotation is not None else (str | None)
            fields_any[name] = (
                underlying,
                Field(
                    description=info.description,
                    default=info.default,
                    json_schema_extra={"enum": enum_with_null},
                ),
            )
        else:
            # Preserve original
            if annotation is None:
                fields_any[name] = (Any, Field(default=info.default))
            else:
                fields_any[name] = (annotation, Field(default=info.default))

    # Build a fresh model solely for schema purposes (we validate with real classes later)
    # Help type checker: pydantic's create_model accepts field tuples via **kwargs
    fields_any_typed: dict[str, Any] = cast(dict[str, Any], fields_any)
    constrained = create_model(  # type: ignore[call-arg]
        f"{action_class.__name__}",
        **fields_any_typed,
    )
    return constrained  # type: ignore[return-value]


# Note: We avoid creating dynamic Enum types to keep type-checkers and
# JSON schema generation happy across environments. We rely on json_schema_extra
# to convey the allowed values to the LLM via response_format.

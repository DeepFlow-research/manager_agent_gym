"""
LLM Action Utilities for Manager Agents.

Simple utility functions for building LLM constraints and action descriptions
without the overhead of a registry class.
"""

from typing import Type, Union
from pydantic import BaseModel, Field

from manager_agent_gym.core.agents.manager_agent.actions import BaseManagerAction
from manager_agent_gym.core.agents.manager_agent.actions import (
    AssignTaskAction,
    CreateTaskAction,
    RemoveTaskAction,
    RefineTaskAction,
    AddTaskDependencyAction,
    RemoveTaskDependencyAction,
    InspectTaskAction,
    DecomposeTaskAction,
    SendMessageAction,
    NoOpAction,
    GetWorkflowStatusAction,
    GetAvailableAgentsAction,
    GetPendingTasksAction,
)


def build_action_constraint_schema(
    action_classes: list[type[BaseManagerAction]],
) -> Type[BaseModel]:
    """
    Build Pydantic constraint schema for LLM structured output.

    Args:
        action_classes: List of action classes that inherit from BaseManagerAction

    Returns:
        Pydantic model that constrains LLM to valid actions
    """
    # Build Union type explicitly using typing.Union
    action_union = (
        Union[tuple(action_classes)] if len(action_classes) > 1 else action_classes[0]
    )

    class ConstrainedManagerAction(BaseModel):
        reasoning: str = Field(
            description="Your reasoning for choosing this action to advance the workflow"
        )
        action: action_union = Field(description="The specific action to take")  # type: ignore[valid-type]

    return ConstrainedManagerAction


def get_action_descriptions(
    action_classes: list[type[BaseManagerAction]],
) -> dict[str, str]:
    """
    Extract descriptions from action class docstrings and field information.

    Args:
        action_classes: List of action classes

    Returns:
        Dictionary mapping action types to descriptions including arguments
    """
    descriptions = {}
    for action_class in action_classes:
        # Get action type from the class using model_fields
        try:
            field_info = action_class.model_fields["action_type"]
            action_type = field_info.default

            if action_type is not None:
                # Extract description from the class docstring
                docstring = action_class.__doc__
                base_description = ""
                if docstring:
                    # Take the first line of the docstring, stripped of whitespace
                    base_description = docstring.strip().split("\n")[0]
                else:
                    # Fallback if no docstring is found
                    base_description = f"Action type: {action_type}"

                # Extract field information (excluding action_type and inherited fields)
                field_descriptions = []
                for field_name, field_info in action_class.model_fields.items():
                    # Skip action_type and fields inherited from BaseManagerAction
                    if field_name in [
                        "action_type",
                        "success",
                        "result_summary",
                        "reasoning",
                    ]:
                        continue

                    # Get field type annotation
                    field_type = "unknown"
                    try:
                        if field_info.annotation:
                            field_type = str(field_info.annotation)
                            # Clean up type annotation for readability
                            field_type = (
                                field_type.replace("typing.", "")
                                .replace("<class '", "")
                                .replace("'>", "")
                            )
                    except AttributeError:
                        field_type = "unknown"

                    # Get field description from Field() if available
                    field_desc = ""
                    try:
                        if field_info.description:
                            field_desc = field_info.description
                    except AttributeError:
                        field_desc = ""

                    # Get default value if available
                    default_info = ""
                    try:
                        if field_info.default is not None and field_info.default != ...:
                            # ... is Ellipsis, means required field
                            default_info = f" (default: {field_info.default})"
                    except AttributeError:
                        default_info = ""

                    # Format the field description
                    field_line = f"  - {field_name}: {field_type}"
                    if field_desc:
                        field_line += f" - {field_desc}"
                    if default_info:
                        field_line += default_info

                    field_descriptions.append(field_line)

                # Combine base description with field descriptions
                full_description = base_description
                if field_descriptions:
                    full_description += "\n  Arguments:"
                    full_description += "\n" + "\n".join(field_descriptions)

                descriptions[action_type] = full_description

        except (AttributeError, KeyError):
            # Skip classes that don't have proper action_type field
            continue

    return descriptions


def get_default_action_classes() -> list[type[BaseManagerAction]]:
    """
    Get the default set of action classes.

    Returns:
        List of default action classes including hierarchical task decomposition capabilities
    """

    return [
        # Task assignment and basic workflow actions
        AssignTaskAction,
        CreateTaskAction,
        RemoveTaskAction,
        # Hierarchical task decomposition and editing
        RefineTaskAction,
        AddTaskDependencyAction,
        RemoveTaskDependencyAction,
        DecomposeTaskAction,
        # Observability-increasing actions
        InspectTaskAction,
        GetWorkflowStatusAction,
        GetAvailableAgentsAction,
        GetPendingTasksAction,
        # Communication and control
        SendMessageAction,
        # RequestEndWorkflowAction,
        NoOpAction,
    ]

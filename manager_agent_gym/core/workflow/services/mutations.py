"""
Workflow mutation operations - state changes to workflow.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from manager_agent_gym.schemas.domain.workflow import Workflow
    from manager_agent_gym.schemas.domain.task import Task
    from manager_agent_gym.schemas.domain.resource import Resource
    from manager_agent_gym.core.agents.workflow_agents.common.interface import (
        AgentInterface,
    )


class WorkflowMutations:
    """Stateless mutation service for workflow state changes."""

    @staticmethod
    def add_task(workflow: "Workflow", task: "Task") -> None:
        """Add a task to the workflow."""
        workflow.tasks[task.id] = task

    @staticmethod
    def add_resource(workflow: "Workflow", resource: "Resource") -> None:
        """Add a resource to the workflow."""
        workflow.resources[resource.id] = resource

    @staticmethod
    def add_agent(workflow: "Workflow", agent: "AgentInterface") -> None:
        """Add an agent to the workflow."""
        workflow.agents[agent.agent_id] = agent

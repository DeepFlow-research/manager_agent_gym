"""
Agent interfaces and implementations for Manager Agent Gym.

This module provides the core agent abstractions for executing tasks
in the workflow system.
"""

from manager_agent_gym.core.agents.workflow_agents.common.interface import (
    AgentInterface,
)

from manager_agent_gym.core.agents.workflow_agents.tools.registry import (
    AgentRegistry,
)

from manager_agent_gym.core.agents.workflow_agents.workers.ai_agent import (
    AIAgent,
)

from manager_agent_gym.core.agents.workflow_agents.workers.human_agent import (
    MockHumanAgent,
)

from manager_agent_gym.core.agents.workflow_agents.tools.tool_factory import (
    ToolFactory,
)


__all__ = [
    "AgentInterface",
    "AgentRegistry",
    "AIAgent",
    "MockHumanAgent",
    "ToolFactory",
]

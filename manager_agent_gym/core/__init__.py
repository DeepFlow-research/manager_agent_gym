"""
Core functionality for Manager Agent Gym.

This module provides access to the core submodules while preserving
the organized folder structure. Import specific functionality from
the appropriate submodules:

- manager_agent: StructuredManagerAgent, ManagerAgent
- workflow_agents: AgentRegistry, AIAgent, MockHumanAgent
- execution: WorkflowExecutionEngine, workflow_builder
- evaluation: NestedPreferenceRegretCalculator
- communication: CommunicationService
- decomposition: Task decomposition services
- common: Shared utilities (logging, LLM interface)
"""

# Only expose the submodules, not individual classes
# This preserves the folder structure and encourages proper imports

from . import manager_agent
from . import workflow_agents
from . import execution
from . import communication
from . import decomposition
from . import common

__all__ = [
    "manager_agent",
    "workflow_agents",
    "execution",
    "communication",
    "decomposition",
    "common",
]

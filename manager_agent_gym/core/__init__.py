"""
Core functionality for Manager Agent Gym.

This module provides access to the core submodules while preserving
the organized folder structure. Import specific functionality from
the appropriate submodules:

- agents.manager_agent: ChainOfThoughtManagerAgent, ManagerAgent
- agents.workflow_agents: AgentRegistry, AIAgent, MockHumanAgent
- agents.stakeholder_agent: StakeholderAgent, ClarificationStakeholderAgent
- workflow: WorkflowExecutionEngine, workflow services
- evaluation: NestedPreferenceRegretCalculator
- communication: CommunicationService
- common: Shared utilities (logging, LLM interface)
"""

from manager_agent_gym.core import agents
from manager_agent_gym.core import workflow
from manager_agent_gym.core import communication
from manager_agent_gym.core import common


__all__ = [
    "agents",
    "workflow",
    "communication",
    "common",
]

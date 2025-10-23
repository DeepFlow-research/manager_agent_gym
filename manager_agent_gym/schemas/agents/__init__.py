"""
Agent configuration schemas.

This module provides data structures for configuring AI agents, human mock agents,
and stakeholder agents in the workflow system.
"""

from manager_agent_gym.schemas.agents.base import (
    AgentConfig,
    AIAgentConfig,
    HumanAgentConfig,
)
from manager_agent_gym.schemas.agents.outputs import (
    AITaskOutput,
    HumanWorkOutput,
    HumanTimeEstimation,
)
from manager_agent_gym.schemas.agents.stakeholder import (
    StakeholderConfig,
    StakeholderPublicProfile,
    StakeholderPreferenceState,
)

__all__ = [
    "AgentConfig",
    "AIAgentConfig",
    "HumanAgentConfig",
    "AITaskOutput",
    "HumanWorkOutput",
    "HumanTimeEstimation",
    "StakeholderConfig",
    "StakeholderPublicProfile",
    "StakeholderPreferenceState",
]

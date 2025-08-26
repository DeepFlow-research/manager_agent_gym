"""
Agent-related data models and configurations.

This module provides data structures for agent configuration,
task execution context, and results.
"""

from .config import AgentConfig, AIAgentConfig, HumanAgentConfig
from .outputs import AITaskOutput, HumanWorkOutput, HumanTimeEstimation
from .stakeholder import StakeholderConfig, StakeholderPublicProfile

__all__ = [
    "AgentConfig",
    "AIAgentConfig",
    "HumanAgentConfig",
    "AITaskOutput",
    "HumanWorkOutput",
    "HumanTimeEstimation",
    "StakeholderConfig",
    "StakeholderPublicProfile",
]

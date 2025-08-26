"""
Agent interfaces and implementations for Manager Agent Gym.

This module provides the core agent abstractions for executing tasks
in the workflow system.
"""

from .interface import (
    AgentInterface,
)

from .registry import (
    AgentRegistry,
)

from .ai_agent import (
    AIAgent,
)

from .human_agent import (
    MockHumanAgent,
)

from .tool_factory import (
    ToolFactory,
)


__all__ = [
    "AgentInterface",
    "AgentRegistry",
    "AIAgent",
    "MockHumanAgent",
    "ToolFactory",
]

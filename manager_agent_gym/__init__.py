"""
Manager Agent Gym - A framework for simulating and evaluating manager agents in workflow environments.

This package provides a comprehensive framework for creating, executing, and evaluating
autonomous manager agents in workflow environments.

Key Components:
- ChainOfThoughtManagerAgent: Main LLM-based manager implementation
- WorkflowExecutionEngine: Engine for running workflows
- AgentRegistry: Registry for workflow agents
- Workflow building utilities and examples
"""

__version__ = "0.1.0"

# Import core submodules for advanced usage
from . import schemas
from . import core

# Import key classes and functions for easy access
from .core.manager_agent import ChainOfThoughtManagerAgent, ManagerAgent
from .core.workflow_agents import AgentRegistry
from .core.execution.engine import WorkflowExecutionEngine
from .core.communication import CommunicationService

# Import key schemas for workflow creation
from .schemas.core import (
    Workflow,
    Task,
    Resource,
    TaskStatus,
    Message,
)
from .schemas.preferences.preference import Preference, PreferenceWeights

# Import execution schemas
from .schemas.execution import (
    ExecutionState,
)

__all__ = [
    # Version
    "__version__",
    # Submodules
    "schemas",
    "core",
    # Core functionality
    "ChainOfThoughtManagerAgent",
    "ManagerAgent",
    "AgentRegistry",
    "WorkflowExecutionEngine",
    "CommunicationService",
    # Core schemas
    "Workflow",
    "Task",
    "Resource",
    "TaskStatus",
    "Preference",
    "PreferenceWeights",
    "Message",
    # Execution schemas
    "ExecutionState",
]

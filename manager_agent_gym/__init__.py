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

# Import core submodules for advanced usage (lazy imports to avoid circular dependencies)
# from . import schemas
# from . import core

# Import key classes and functions for easy access (commented to avoid circular imports during module initialization)
# These can be imported directly from their respective modules when needed
# from .core.agents.manager_agent.implementations.chain_of_thought import ChainOfThoughtManagerAgent
# from .core.agents.manager_agent.common.interface import ManagerAgent
# from .core.agents.workflow_agents import AgentRegistry
# from .core.workflow.engine import WorkflowExecutionEngine
# from .core.communication import CommunicationService
# from .schemas.domain import Workflow, Task, Resource, TaskStatus, Message
# from .schemas.preferences.preference import Preference, PreferenceSnapshot
# from .core.execution.schemas import ExecutionState

__all__ = [
    # Version
    "__version__",
]

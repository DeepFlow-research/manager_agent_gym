"""Communication tools - two implementations.

- communication.py: Factory-based approach with two-layer architecture
- communication_di.py: DI-based approach using RunContextWrapper
"""

from manager_agent_gym.core.agents.workflow_agents.tools.communication.communication import (
    create_communication_tools,
)
from manager_agent_gym.core.agents.workflow_agents.tools.communication.communication_di import (
    COMMUNICATION_TOOLS,
    send_message,
    broadcast_message,
    get_recent_messages,
    end_workflow,
)

__all__ = [
    "create_communication_tools",
    "COMMUNICATION_TOOLS",
    "send_message",
    "broadcast_message",
    "get_recent_messages",
    "end_workflow",
]

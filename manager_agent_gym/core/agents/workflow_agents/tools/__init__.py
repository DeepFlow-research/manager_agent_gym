"""Tools module - flat structure with two-layer architecture.

New architecture:
- Layer 1: Core functions (_*) - pure business logic, fully testable
- Layer 2: OpenAI tool wrappers - thin adapters for OpenAI SDK

All tools are in flat files:
- documents.py: PDF, DOCX, Markdown operations
- spreadsheets.py: Excel, CSV, Chart operations
- code.py: Python and JavaScript code execution
- ocr.py: Image and PDF OCR
- rag.py: Retrieval-augmented generation
- web_search.py: Web search with Exa + Cohere
- communication.py: Agent communication
- thinking.py: Thinking and planning tools for task execution
"""

# Flat tool modules
from manager_agent_gym.core.agents.workflow_agents.tools.documents import (
    create_documents_tools,
)
from manager_agent_gym.core.agents.workflow_agents.tools.spreadsheets import (
    create_spreadsheets_tools,
)
from manager_agent_gym.core.agents.workflow_agents.tools.code import create_code_tools
from manager_agent_gym.core.agents.workflow_agents.tools.ocr import create_ocr_tools
from manager_agent_gym.core.agents.workflow_agents.tools.rag import create_rag_tools
from manager_agent_gym.core.agents.workflow_agents.tools.web_search import (
    get_search_context,
)
from manager_agent_gym.core.agents.workflow_agents.tools.communication import (
    create_communication_tools,
)
from manager_agent_gym.core.agents.workflow_agents.tools.thinking import (
    create_thinking_tools,
)


def create_web_search_tools():
    """Create web search tools."""
    return [get_search_context]


__all__ = [
    "create_documents_tools",
    "create_spreadsheets_tools",
    "create_code_tools",
    "create_ocr_tools",
    "create_rag_tools",
    "create_web_search_tools",
    "create_communication_tools",
    "create_thinking_tools",
]

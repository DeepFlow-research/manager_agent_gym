"""
Tool factory for creating agent tools.

Centralizes tool creation and management for different agent types.
"""

from typing import TYPE_CHECKING

from agents import Tool, function_tool

if TYPE_CHECKING:
    from manager_agent_gym.core.communication.service import CommunicationService
    from manager_agent_gym.core.workflow.resource_storage import ResourceFileManager


class ToolFactory:
    """Factory for creating and managing agent tools."""

    @staticmethod
    def create_basic_tools() -> list[Tool]:
        """Create basic tools available to all agents."""

        @function_tool
        async def search_information(query: str = "default query") -> str:
            """
            Search for information on a given topic.

            Args:
                query: The search query

            Returns:
                Search results as text
            """
            return f"Search results for '{query}': [Simulated search results would appear here]"

        @function_tool
        async def analyze_data(data: str = "no data provided") -> str:
            """
            Analyze the provided data and extract insights.

            Args:
                data: The data to analyze

            Returns:
                Analysis results
            """
            return f"Analysis of data: [Simulated analysis of: {data[:100]}...]"

        # Defer import to avoid import-time cycles
        from manager_agent_gym.core.agents.workflow_agents.tools.web_search import (
            get_search_context,
        )
        from manager_agent_gym.core.agents.workflow_agents.tools.thinking import (
            create_thinking_tools,
        )

        return [
            search_information,
            analyze_data,
            get_search_context,
        ] + create_thinking_tools()

    @staticmethod
    def create_human_tools() -> list[Tool]:
        """Create tools specific to human mock agents."""
        tools = ToolFactory.create_basic_tools()

        @function_tool
        async def take_break(duration_minutes: int = 15) -> str:
            """
            Take a break from work (human behavior simulation).

            Args:
                duration_minutes: Length of break in minutes

            Returns:
                Break completion message
            """
            return f"Took a {duration_minutes}-minute break. Feeling refreshed!"

        @function_tool
        async def consult_colleague(topic: str = "general question") -> str:
            """
            Consult with a colleague about a work topic.

            Args:
                topic: The topic to discuss

            Returns:
                Colleague's advice
            """
            return f"Discussed '{topic}' with colleague. Got some helpful insights."

        tools.extend([take_break, consult_colleague])
        return tools

    @staticmethod
    def create_ai_tools() -> list[Tool]:
        """Create tools specific to AI agents."""
        tools = ToolFactory.create_basic_tools()

        @function_tool
        async def generate_code(description: str = "basic function") -> str:
            """
            Generate code based on a description.

            Args:
                description: Description of what the code should do

            Returns:
                Generated code
            """
            return f"```python\n# Generated code for: {description}\npass\n```"

        @function_tool
        async def calculate_metrics(data: str = "no data") -> str:
            """
            Calculate performance metrics from data.

            Args:
                data: Input data for metrics calculation

            Returns:
                Calculated metrics
            """
            return "Metrics calculated for data: [Accuracy: 95%, Performance: Good]"

        tools.extend([generate_code, calculate_metrics])
        return tools

    @staticmethod
    def add_communication_tools(
        tools: list[Tool], communication_service: "CommunicationService", agent_id: str
    ) -> list[Tool]:
        """
        Add communication tools to an existing tool list.

        Args:
            tools: Existing tools to add communication tools to
            communication_service: The communication service instance
            agent_id: The ID of the agent using these tools

        Returns:
            Enhanced tool list with communication capabilities
        """
        # Defer import to avoid import-time cycles
        from manager_agent_gym.core.agents.workflow_agents.tools.communication import (
            create_communication_tools,
        )

        comm_tools = create_communication_tools(
            communication_service=communication_service,
            agent_id=agent_id,
            current_task_id=None,  # Will be set dynamically during task execution
        )

        return tools + comm_tools

    @staticmethod
    def create_gdpeval_tools(
        resource_manager: "ResourceFileManager | None" = None,
        e2b_api_key: str | None = None,
    ) -> list[Tool]:
        """
        Create comprehensive GDPEval toolkit.

        Includes tools for document processing (PDF/DOCX), spreadsheets (Excel/CSV),
        RAG-based document search, OCR, code execution, and chart generation.

        Args:
            resource_manager: File storage manager for handling resources.
                             If None, creates a default instance.
            e2b_api_key: E2B API key for code execution. If None, loads from config.

        Returns:
            List of all GDPEval tools
        """
        # Import resource manager if needed
        if resource_manager is None:
            from manager_agent_gym.core.workflow.resource_storage import (
                ResourceFileManager,
            )

            resource_manager = ResourceFileManager()

        # Load E2B API key from config if not provided
        if e2b_api_key is None:
            from manager_agent_gym.config import get_settings

            settings = get_settings()
            e2b_api_key = settings.E2B_API_KEY if settings.E2B_API_KEY != "na" else None

        # Import tool creation functions from new flat structure
        from manager_agent_gym.core.agents.workflow_agents.tools.documents import (
            create_documents_tools,
        )
        from manager_agent_gym.core.agents.workflow_agents.tools.spreadsheets import (
            create_spreadsheets_tools,
        )
        from manager_agent_gym.core.agents.workflow_agents.tools.rag import (
            create_rag_tools,
        )
        from manager_agent_gym.core.agents.workflow_agents.tools.ocr import (
            create_ocr_tools,
        )
        from manager_agent_gym.core.agents.workflow_agents.tools.code import (
            create_code_tools,
        )
        from manager_agent_gym.core.agents.workflow_agents.tools.web_search import (
            get_search_context,
        )

        # Create all tool sets
        tools: list[Tool] = []

        # Document tools (all-in-one from flat structure)
        tools.extend(create_documents_tools(resource_manager))

        # Spreadsheet tools (all-in-one from flat structure)
        tools.extend(create_spreadsheets_tools(resource_manager))

        # Code execution tools
        tools.extend(create_code_tools(resource_manager, e2b_api_key))

        # OCR tools
        tools.extend(create_ocr_tools(resource_manager))

        # RAG tools
        tools.extend(create_rag_tools(resource_manager))

        # Web search
        tools.append(get_search_context)

        # Thinking tools
        from manager_agent_gym.core.agents.workflow_agents.tools.thinking import (
            create_thinking_tools,
        )

        tools.extend(create_thinking_tools())

        return tools

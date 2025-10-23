"""
Integration tests for tool factory.

Tests that all tools can be created successfully and have proper structure.
"""

import pytest

from manager_agent_gym.core.agents.workflow_agents.tools.tool_factory import ToolFactory
from manager_agent_gym.core.workflow.resource_storage import ResourceFileManager


# ============================================================================
# TOOL FACTORY TESTS
# ============================================================================


def test_create_basic_tools() -> None:
    """Test creating basic tools."""
    tools = ToolFactory.create_basic_tools()

    assert len(tools) > 0
    assert all(hasattr(tool, "name") for tool in tools)
    assert all(hasattr(tool, "description") for tool in tools)


def test_create_human_tools() -> None:
    """Test creating human-specific tools."""
    tools = ToolFactory.create_human_tools()

    assert len(tools) > 0
    assert all(hasattr(tool, "name") for tool in tools)


def test_create_ai_tools() -> None:
    """Test creating AI-specific tools."""
    tools = ToolFactory.create_ai_tools()

    assert len(tools) > 0
    assert all(hasattr(tool, "name") for tool in tools)


def test_create_gdpeval_tools() -> None:
    """Test creating GDPEval tools."""
    resource_manager = ResourceFileManager()
    tools = ToolFactory.create_gdpeval_tools(resource_manager=resource_manager)

    assert len(tools) > 0
    assert all(hasattr(tool, "name") for tool in tools)

    # Check that we have tools from different categories
    tool_names = [tool.name for tool in tools]

    # Document tools
    assert any("pdf" in name.lower() or "docx" in name.lower() for name in tool_names)

    # Spreadsheet tools
    assert any("excel" in name.lower() or "csv" in name.lower() for name in tool_names)

    # Code execution tools
    assert any(
        "python" in name.lower() or "code" in name.lower() for name in tool_names
    )

    # OCR tools
    assert any("ocr" in name.lower() or "image" in name.lower() for name in tool_names)

    # RAG tools
    assert any(
        "index" in name.lower() or "search" in name.lower() for name in tool_names
    )


def test_create_gdpeval_tools_without_resource_manager() -> None:
    """Test creating GDPEval tools with default resource manager."""
    tools = ToolFactory.create_gdpeval_tools()

    assert len(tools) > 0


def test_create_gdpeval_tools_without_e2b_key() -> None:
    """Test creating GDPEval tools without E2B API key."""
    resource_manager = ResourceFileManager()
    tools = ToolFactory.create_gdpeval_tools(
        resource_manager=resource_manager, e2b_api_key=None
    )

    assert len(tools) > 0


# ============================================================================
# COMMUNICATION TOOLS TESTS
# ============================================================================


def test_add_communication_tools() -> None:
    """Test adding communication tools to existing tools."""
    from manager_agent_gym.core.communication.service import CommunicationService

    basic_tools = ToolFactory.create_basic_tools()
    initial_count = len(basic_tools)

    comm_service = CommunicationService()
    enhanced_tools = ToolFactory.add_communication_tools(
        basic_tools, comm_service, "test_agent"
    )

    assert len(enhanced_tools) > initial_count
    tool_names = [tool.name for tool in enhanced_tools]
    assert any("message" in name.lower() for name in tool_names)


# ============================================================================
# TOOL STRUCTURE TESTS
# ============================================================================


def test_all_tools_have_required_attributes() -> None:
    """Test that all tools have required attributes."""
    resource_manager = ResourceFileManager()
    all_tools = []

    all_tools.extend(ToolFactory.create_basic_tools())
    all_tools.extend(ToolFactory.create_human_tools())
    all_tools.extend(ToolFactory.create_ai_tools())
    all_tools.extend(
        ToolFactory.create_gdpeval_tools(resource_manager=resource_manager)
    )

    for tool in all_tools:
        # Check required attributes
        assert hasattr(tool, "name"), "Tool missing 'name' attribute"
        assert hasattr(tool, "description"), f"Tool {tool.name} missing 'description'"

        # Check name is valid
        assert isinstance(tool.name, str), "Tool name must be string"
        assert len(tool.name) > 0, "Tool name cannot be empty"

        # Check description is valid
        assert isinstance(tool.description, str), (
            f"Tool {tool.name} description must be string"
        )
        assert len(tool.description) > 0, (
            f"Tool {tool.name} description cannot be empty"
        )


def test_no_duplicate_tool_names() -> None:
    """Test that there are no duplicate tool names in GDPEval toolkit."""
    resource_manager = ResourceFileManager()
    tools = ToolFactory.create_gdpeval_tools(resource_manager=resource_manager)

    tool_names = [tool.name for tool in tools]
    unique_names = set(tool_names)

    assert len(tool_names) == len(unique_names), "Found duplicate tool names"


# ============================================================================
# CROSS-TOOL WORKFLOW TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_document_to_spreadsheet_workflow(tmp_path) -> None:
    """Test workflow: create document, then create spreadsheet with extracted data."""
    from manager_agent_gym.core.agents.workflow_agents.tools.documents import (
        _save_markdown,
    )
    from manager_agent_gym.core.agents.workflow_agents.tools.spreadsheets import (
        _create_excel,
        ExcelData,
    )

    # Step 1: Create a markdown document
    md_path = tmp_path / "data.md"
    md_content = "# Test Data\n\n- Item 1\n- Item 2\n- Item 3"

    md_result = await _save_markdown(md_content, str(md_path))
    assert md_result["success"] is True

    # Step 2: Create an Excel file with the data
    excel_path = tmp_path / "data.xlsx"
    excel_data = ExcelData(
        headers=["Item", "Count"], rows=[["Item 1", 1], ["Item 2", 2], ["Item 3", 3]]
    )

    excel_result = await _create_excel(excel_data, str(excel_path))
    assert excel_result["success"] is True

    # Both files should exist
    assert md_path.exists()
    assert excel_path.exists()


@pytest.mark.asyncio
@pytest.mark.requires_rag
async def test_rag_search_workflow(sample_text_file) -> None:
    """Test workflow: index document, then search it."""
    from manager_agent_gym.core.agents.workflow_agents.tools.rag import (
        _index_documents,
        _search_documents,
    )

    # Step 1: Index the document
    index_result = await _index_documents([str(sample_text_file)])
    assert index_result["success"] is True
    index_id = index_result["index_id"]

    # Step 2: Search the indexed document
    search_result = await _search_documents("test", index_id, top_k=3)
    assert search_result["success"] is True

"""Test script for Phase 2 worker tools."""

import asyncio
import json
import tempfile
from pathlib import Path

print("Phase 2 Tools Test - Starting...")


async def test_tools():
    """Quick test of tools."""
    from manager_agent_gym.core.agents.workflow_agents.tools.spreadsheets.excel_tools import (
        create_excel_tools,
    )
    from manager_agent_gym.core.workflow.resource_storage import ResourceFileManager

    # Create temp dir
    temp_dir = Path(tempfile.mkdtemp(prefix="test_"))
    resource_manager = ResourceFileManager(temp_dir)

    # Get Excel tools
    tools = create_excel_tools(resource_manager)
    create_excel = tools[1]

    # Test data
    data = {"headers": ["A", "B", "C"], "rows": [[1, 2, 3], [4, 5, 6]]}

    # Call tool
    result = await create_excel(
        data=data, output_path=str(temp_dir / "test.xlsx"), sheet_name="Test"
    )

    # Parse result
    result_json = json.loads(result)

    print("\n✓ Tool Result:")
    print(json.dumps(result_json, indent=2))

    if result_json.get("success"):
        print("\n✓✓✓ TEST PASSED - Tool returns rich context!")
        return True
    else:
        print(f"\n❌ TEST FAILED - {result_json.get('error')}")
        return False


if __name__ == "__main__":
    success = asyncio.run(test_tools())
    exit(0 if success else 1)

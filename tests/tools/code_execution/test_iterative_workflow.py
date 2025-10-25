"""Test iterative workflow support for execute_python_code.

This test verifies that files created in one execute_python_code call
are available in subsequent calls (the bug fix for sandbox file persistence).
"""

import pytest
from unittest.mock import MagicMock
from uuid import uuid4

from manager_agent_gym.core.workflow.context import AgentExecutionContext
from manager_agent_gym.schemas.domain.resource import Resource
from manager_agent_gym.core.communication.service import CommunicationService


@pytest.mark.asyncio
async def test_intermediary_resources_uploaded_to_sandbox():
    """Test that intermediary resources (files created in previous calls) are uploaded to sandbox."""

    # Create mock context with initial input resource
    # Note: resource_role must be "output" or "intermediary" per schema
    initial_resource = Resource(
        name="Input Data",
        description="Initial input file provided to task",
        file_path="/tmp/initial_input.xlsx",
        mime_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        size_bytes=1000,
        resource_role="output",  # Initial task inputs are marked as "output" from previous tasks
    )

    # Create context
    context = AgentExecutionContext(
        communication_service=MagicMock(spec=CommunicationService),
        agent_id="test_agent",
        current_task_id=uuid4(),
        input_resources=[initial_resource],
        intermediary_resources=[],
    )

    # Simulate what happens after first execute_python_code call:
    # File gets created and registered as intermediary resource
    created_resource = Resource(
        name="Generated: output.xlsx",
        description="Auto-created by code execution",
        file_path="/tmp/e2b_output_123/output.xlsx",
        mime_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        size_bytes=2000,
        resource_role="intermediary",
    )
    context.register_created_resource(created_resource)

    # Verify intermediary resource was registered
    assert len(context.intermediary_resources) == 1
    assert (
        context.intermediary_resources[0].file_path == "/tmp/e2b_output_123/output.xlsx"
    )

    # THE KEY TEST: get_all_available_resources should return BOTH
    all_resources = context.get_all_available_resources()
    assert len(all_resources) == 2

    # Should include initial input
    assert initial_resource in all_resources
    # Should include intermediary (created) file
    assert created_resource in all_resources

    # Extract file paths (this is what execute_python_code does)
    file_paths = [r.file_path for r in all_resources if r.file_path]

    # CRITICAL: Both files should be in the list for upload
    assert "/tmp/initial_input.xlsx" in file_paths
    assert "/tmp/e2b_output_123/output.xlsx" in file_paths

    print("✅ Test passed: Intermediary resources are included for upload to sandbox")


@pytest.mark.asyncio
async def test_multiple_intermediary_resources_accumulate():
    """Test that multiple intermediary resources accumulate across calls."""

    context = AgentExecutionContext(
        communication_service=MagicMock(spec=CommunicationService),
        agent_id="test_agent",
        current_task_id=uuid4(),
        input_resources=[],
        intermediary_resources=[],
    )

    # Simulate 3 sequential execute_python_code calls, each creating a file
    for i in range(3):
        resource = Resource(
            name=f"Generated: file_{i}.xlsx",
            description="Auto-created by code execution",
            file_path=f"/tmp/output/file_{i}.xlsx",
            mime_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            size_bytes=1000 * (i + 1),
            resource_role="intermediary",
        )
        context.register_created_resource(resource)

        # After each registration, all previous files should still be available
        all_resources = context.get_all_available_resources()
        assert len(all_resources) == i + 1

    # Final check: all 3 files should be available for upload
    final_resources = context.get_all_available_resources()
    assert len(final_resources) == 3

    file_paths = [r.file_path for r in final_resources]
    assert "/tmp/output/file_0.xlsx" in file_paths
    assert "/tmp/output/file_1.xlsx" in file_paths
    assert "/tmp/output/file_2.xlsx" in file_paths

    print("✅ Test passed: Multiple intermediary resources accumulate correctly")


if __name__ == "__main__":
    import asyncio

    print("Running iterative workflow tests...")
    asyncio.run(test_intermediary_resources_uploaded_to_sandbox())
    asyncio.run(test_multiple_intermediary_resources_accumulate())
    print("\n✅ All tests passed!")

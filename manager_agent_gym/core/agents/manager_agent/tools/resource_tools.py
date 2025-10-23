"""
Manager resource inspection tools for multimodal content.

These tools allow manager agents to visually inspect resources
(images, PDFs, Excel files) created by worker agents.
"""

from agents import function_tool

from manager_agent_gym.core.workflow.context import AgentExecutionContext
from manager_agent_gym.core.common.logging import logger


@function_tool
async def inspect_resource_visually(
    resource_id: str,
    detail_level: str = "high",
    context: AgentExecutionContext | None = None,
) -> str:
    """Inspect a resource visually (for images, PDFs, Excel).

    Use this tool to view the actual visual content of a resource
    (images, PDF pages, Excel sheets rendered as tables).

    Args:
        resource_id: The UUID of the resource to inspect
        detail_level: Detail level - "high" for detailed analysis, "low" for faster inspection
        context: Execution context (injected automatically)

    Returns:
        Description of the visual content with multimodal rendering
    """
    try:
        # Note: Full implementation requires access to workflow state
        # This is a placeholder that demonstrates the tool structure
        # In production, this would:
        # 1. Get resource from workflow via context
        # 2. Use MultimodalResourceProcessor to render it
        # 3. Return formatted visual content or description

        logger.info(f"Manager inspecting resource visually: {resource_id}")

        return (
            f"Resource inspection tool called for {resource_id} at detail level {detail_level}. "
            f"Full implementation requires workflow context integration."
        )

    except Exception as e:
        logger.error(f"Error inspecting resource {resource_id}: {e}")
        return f"Error inspecting resource: {str(e)}"


@function_tool
async def read_resource_text(
    resource_id: str,
    max_chars: int = 5000,
    context: AgentExecutionContext | None = None,
) -> str:
    """Read text content from a resource.

    Use this tool to read the text content of text-based resources
    (markdown, JSON, CSV files, etc.).

    Args:
        resource_id: The UUID of the resource to read
        max_chars: Maximum characters to return
        context: Execution context (injected automatically)

    Returns:
        Text content of the resource
    """
    try:
        logger.info(f"Manager reading text from resource: {resource_id}")

        # Placeholder implementation
        return (
            f"Text reading tool called for {resource_id} (max {max_chars} chars). "
            f"Full implementation requires workflow context integration."
        )

    except Exception as e:
        logger.error(f"Error reading resource {resource_id}: {e}")
        return f"Error reading resource: {str(e)}"


@function_tool
async def list_resources_for_task(
    task_id: str,
    context: AgentExecutionContext | None = None,
) -> str:
    """List all resources (outputs) created by a specific task.

    Use this tool to see what outputs a completed task has produced.

    Args:
        task_id: The UUID of the task
        context: Execution context (injected automatically)

    Returns:
        List of resources with their IDs, names, and types
    """
    try:
        logger.info(f"Manager listing resources for task: {task_id}")

        # Placeholder implementation
        return (
            f"Resource listing tool called for task {task_id}. "
            f"Full implementation requires workflow context integration."
        )

    except Exception as e:
        logger.error(f"Error listing resources for task {task_id}: {e}")
        return f"Error listing resources: {str(e)}"


# Tool registry for easy access
MANAGER_RESOURCE_TOOLS = [
    inspect_resource_visually,
    read_resource_text,
    list_resources_for_task,
]

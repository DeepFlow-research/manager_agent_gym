"""
AI Agent implementation using OpenAI Agents SDK.

Provides real LLM-powered agents that can execute tasks using
system prompts and tools via the OpenAI Agents framework.
"""

import os
import time
import traceback
from typing import TYPE_CHECKING
from agents import Agent, Runner, Tool, RunResult
from agents.extensions.models.litellm_model import LitellmModel

if TYPE_CHECKING:
    from manager_agent_gym.core.common.llm_generator import LLMGenerator


from manager_agent_gym.config import settings
from litellm.cost_calculator import cost_per_token

from manager_agent_gym.schemas.domain import Resource, Task
from manager_agent_gym.schemas.domain.communication import Message, MessageType
from manager_agent_gym.schemas.agents import (
    AIAgentConfig,
    AITaskOutput,
)
from manager_agent_gym.core.execution.schemas.results import (
    ExecutionResult,
    create_task_result,
)
from manager_agent_gym.core.agents.workflow_agents.common.interface import (
    AgentInterface,
)
from manager_agent_gym.core.common.logging import logger


from manager_agent_gym.core.agents.workflow_agents.prompts.ai_agent_prompts import (
    AI_AGENT_TASK_TEMPLATE,
)


class AIAgent(AgentInterface[AIAgentConfig]):
    """
    AI agent implementation using OpenAI Agents SDK.

    Executes tasks using real LLM inference with system prompts
    and structured tools.
    """

    def __init__(
        self,
        config: AIAgentConfig,
        tools: list[Tool],
        llm_generator: "LLMGenerator",
    ):
        if Agent is None or LitellmModel is None or Runner is None:
            raise ImportError(
                "openai-agents SDK is not installed. Install with `uv sync --group agents`."
            )
        super().__init__(config)

        # Ensure OpenAI API key is available in environment
        if settings.OPENAI_API_KEY and settings.OPENAI_API_KEY != "na":
            os.environ["OPENAI_API_KEY"] = settings.OPENAI_API_KEY

        # Include communication tools via late import to avoid circular imports
        from manager_agent_gym.core.agents.workflow_agents.tools.communication.communication_di import (
            COMMUNICATION_TOOLS,
        )
        from manager_agent_gym.core.workflow.context import AgentExecutionContext

        self.tools = tools + COMMUNICATION_TOOLS

        self.openai_agent: Agent[AgentExecutionContext] = Agent(
            model=llm_generator,
            name=config.agent_id,
            instructions=AI_AGENT_TASK_TEMPLATE.format(
                agent_description=config.agent_description,
                agent_capabilities=config.agent_capabilities,
            ),
            tools=self.tools,
        )

    async def execute_task(
        self, task: Task, resources: list[Resource]
    ) -> ExecutionResult:
        """
        Execute a task using the OpenAI Agent.

        Args:
            task: The task to execute
            resources: Available input resources (optional)

        Returns:
            ExecutionResult with AI-generated outputs
        """
        start_time = time.time()

        try:
            # Gather environmental context from messages (rubrics, alerts, etc.)
            context_messages = self._gather_context_messages()

            # Create execution context for dependency injection
            from manager_agent_gym.core.workflow.context import AgentExecutionContext

            if self.communication_service:
                context = AgentExecutionContext(
                    communication_service=self.communication_service,
                    agent_id=self.config.agent_id,
                    current_task_id=task.id,
                    tool_event_sink=self.record_tool_use_event,
                    input_resources=resources or [],
                )
            else:
                # Create a minimal context if no communication service
                from manager_agent_gym.core.communication.service import (
                    CommunicationService,
                )

                context = AgentExecutionContext(
                    communication_service=CommunicationService(),  # Empty service
                    agent_id=self.config.agent_id,
                    current_task_id=task.id,
                    tool_event_sink=self.record_tool_use_event,
                    input_resources=resources or [],
                )

            # Build multimodal input with images/PDFs/Excel
            user_message = await self._build_multimodal_input(
                task, resources or [], context_messages
            )

            # Execute using OpenAI Agent with multimodal content
            result = None  # Initialize to avoid unbound variable error
            try:
                result = await Runner.run(
                    self.openai_agent,
                    [user_message],
                    context=context,
                    max_turns=self.config.max_turns,
                )

                # Extract structured output
                output = result.final_output
                if not isinstance(output, AITaskOutput):
                    raise ValueError(
                        "Output is not an AITaskOutput, falling back to OpenAI parser"
                    )

            except Exception:
                logger.info(
                    "Detected unstructured output from Anthropic model, fixing with OpenAI parser..."
                )

                # If result is None, we can't recover, so re-raise
                if result is None:
                    logger.error("No result from OpenAI Agent, raising exception")
                    raise

                # Serialize the conversation to a string
                import json

                serialized_messages = []
                for msg in result.to_input_list():
                    # Handle different message types
                    if hasattr(msg, "model_dump"):
                        serialized_messages.append(
                            json.dumps(msg.model_dump(), indent=2)  # type: ignore
                        )
                    elif isinstance(msg, dict):
                        serialized_messages.append(json.dumps(msg, indent=2))
                    else:
                        # Fallback to string representation
                        serialized_messages.append(str(msg))

                message_list = "\n\n".join(serialized_messages)

                # Use our fix function to parse it into structured format
                from manager_agent_gym.core.common.llm_generator import (
                    fix_structured_output_with_openai,
                )

                output = await fix_structured_output_with_openai(
                    raw_text_output=message_list,
                    output_schema=AITaskOutput,
                )
                logger.info("Successfully fixed structured output using OpenAI parser")

            # Calculate execution metrics
            execution_time = time.time() - start_time
            output_resources = output.resources

            # MERGE: Combine LLM-created resources with auto-tracked intermediaries
            # This fixes path errors and captures files the LLM forgot to mention
            final_resources = self._merge_llm_and_intermediary_resources(
                llm_resources=output_resources,
                intermediary_resources=context.intermediary_resources,
            )

            # Extract execution trace if enabled
            execution_trace = None
            if self.config.enable_execution_tracing:
                try:
                    from datetime import datetime
                    from manager_agent_gym.core.agents.workflow_agents.utils.trace_extractor import (
                        extract_execution_trace,
                    )

                    started_at = datetime.fromtimestamp(start_time)
                    completed_at = datetime.now()
                    execution_trace = extract_execution_trace(
                        result=result,
                        agent_id=self.config.agent_id,
                        task_id=task.id,
                        started_at=started_at,
                        completed_at=completed_at,
                    )
                except Exception as trace_error:
                    # Don't fail the task if tracing fails
                    logger.warning(
                        f"Failed to extract execution trace: {trace_error}",
                        exc_info=True,
                    )

            # If no resources were created (neither LLM nor intermediary), create a default markdown file
            if not final_resources:
                import tempfile
                from pathlib import Path

                # Save output as markdown file
                temp_dir = Path(tempfile.mkdtemp(prefix="agent_output_"))
                output_file = temp_dir / f"task_{task.id}_output.md"
                output_content = f"# Task Output\n\n{str(result)}"
                output_file.write_text(output_content, encoding="utf-8")

                final_resources.append(
                    Resource(
                        name=f"Completed: {task.name}",
                        description=f"AI agent completed task: {task.description}",
                        file_path=str(output_file.absolute()),
                        mime_type="text/markdown",
                        size_bytes=output_file.stat().st_size,
                    )
                )

            return create_task_result(
                task_id=task.id,
                agent_id=self.config.agent_id,
                success=True,
                execution_time=execution_time,
                resources=final_resources,
                simulated_duration_hours=(execution_time / 3600.0),
                cost=self._calculate_accurate_cost(result),
                execution_notes=output.execution_notes,
                reasoning=output.reasoning,
                execution_trace=execution_trace,
            )

        except Exception as e:
            execution_time = time.time() - start_time

            return create_task_result(
                task_id=task.id,
                agent_id=self.config.agent_id,
                success=False,
                execution_time=execution_time,
                simulated_duration_hours=(execution_time / 3600.0),
                error=traceback.format_exc(),
                resources=[],
                cost=0.0,
                execution_notes=[
                    f"Task execution failed: {traceback.format_exc()}",
                    f"Model: {self.config.model_name}",
                    f"Tools available: {len(self.tools)}",
                    f"Error details: {str(e)}",
                ],
            )

    def _gather_context_messages(self) -> dict[str, list[Message]]:
        """Gather relevant context messages before task execution.

        Returns:
            Dictionary mapping message type categories to message lists.
            Categories: 'rubrics', 'alerts', etc.
        """
        if not self.communication_service:
            return {}

        try:
            # Get all messages and filter for rubrics
            all_messages = self.communication_service.get_messages_for_agent(
                agent_id=self.config.agent_id,
                limit=50,  # Get recent messages
            )
            rubric_messages = [
                msg
                for msg in all_messages
                if msg.message_type == MessageType.RUBRIC_UPDATE
            ][:10]  # Keep most recent 10 rubric messages

            logger.debug(
                f"Agent {self.config.agent_id} gathered {len(rubric_messages)} rubric messages"
            )

            return {
                "rubrics": rubric_messages,
                # Can add more types: 'alerts', 'status_updates', etc.
            }
        except Exception as e:
            logger.warning(
                f"Agent {self.config.agent_id} failed to gather context messages: {e}"
            )
            return {}

    def _format_rubric_messages(self, messages: list[Message]) -> str:
        """Format rubric messages into evaluation criteria section.

        Args:
            messages: List of rubric update messages

        Returns:
            Formatted evaluation criteria section for the prompt template
        """
        if not messages:
            return ""

        rubric_text = "## Evaluation Criteria\n\n"
        rubric_text += "Your work will be assessed against these specific criteria:\n\n"

        for msg in messages:
            pref_name = msg.metadata.get("preference_name", "Quality Standard")
            rubric_text += f"**{pref_name}:**\n{msg.content}\n\n"

        rubric_text += "**Important**: Address each criterion in your work. Document how your approach satisfies these requirements."

        return rubric_text

    def _has_visual_resources(self, resources: list[Resource]) -> bool:
        """Check if any resources contain visual content (images, PDFs, Excel).

        Args:
            resources: List of resources to check

        Returns:
            True if any resource is visual (not plain text)
        """
        for resource in resources:
            if (
                resource.is_image
                or resource.is_document
                or resource.is_spreadsheet
                or not resource.is_text_format
            ):
                return True
        return False

    async def _build_multimodal_input(
        self,
        task: Task,
        resources: list[Resource],
        context_messages: dict[str, list[Message]] | None = None,
    ):
        """Build multimodal input with images/PDFs/Excel for OpenAI Agents SDK.

        Args:
            task: The task to execute
            resources: Available input resources
            context_messages: Optional context from messages (rubrics, etc.)

        Returns:
            Message object with multimodal content
        """
        from manager_agent_gym.core.common.multimodal_resources import (
            MultimodalResourceProcessor,
            create_user_message,
            create_text_content,
        )

        # Create processor with agent's config
        processor = MultimodalResourceProcessor(
            max_tokens=self.config.max_resource_tokens,
            default_image_detail=self.config.image_detail,
        )

        # Build task description text
        task_text = "## Current Assignment\n\n"
        task_text += f"**Task:** {task.name}\n\n"
        task_text += f"**Objective:**\n{task.description}\n\n"

        # Add evaluation criteria if present
        evaluation_criteria = ""
        if context_messages and context_messages.get("rubrics"):
            evaluation_criteria = self._format_rubric_messages(
                context_messages["rubrics"]
            )
            task_text += evaluation_criteria + "\n\n"

        task_text += "**Available Input Resources:**\n"

        # Get resource content blocks (images, PDFs, Excel, text)
        resource_blocks = await processor.format_resources_as_content(
            resources,
            include_metadata=True,
        )

        # Combine task text with resource blocks
        return create_user_message(create_text_content(task_text), *resource_blocks)

    def _format_resources(self, resources: list[Resource]) -> str:
        """Format resources for inclusion in the prompt (text-only fallback)."""
        formatted = []
        for resource in resources:
            # Show file information instead of inline content
            resource_info = [
                f"- {resource.name}: {resource.description}",
                f"  File: {resource.file_path}",
                f"  Type: {resource.mime_type}",
                f"  Size: {resource.size_bytes} bytes",
            ]

            # Add format-specific metadata if available
            if resource.file_format_metadata:
                resource_info.append(f"  Metadata: {resource.file_format_metadata}")

            # Try to show text preview for text-based files
            try:
                if resource.is_text_format:
                    text_preview = resource.load_text()[:200]
                    if len(resource.load_text()) > 200:
                        text_preview += "..."
                    resource_info.append(f"  Preview: {text_preview}")
            except Exception:
                pass  # Skip preview if file can't be read

            formatted.append("\n  ".join(resource_info))

        # Escape all curly braces to prevent .format() from interpreting them as placeholders
        return "\n".join(formatted).replace("{", "{{").replace("}", "}}")

    def _calculate_accurate_cost(self, result: RunResult) -> float:
        """Calculate accurate cost using LiteLLM's cost_per_token function."""
        # Extract token usage details from result
        usage = result.context_wrapper.usage

        # Extract cache token info if available (newer API versions)
        cache_creation_tokens = 0
        cached_tokens = 0
        try:
            if (
                usage.input_tokens_details
                and usage.input_tokens_details.cached_tokens is not None
            ):
                cached_tokens = usage.input_tokens_details.cached_tokens or 0
                cache_creation_tokens = usage.input_tokens - cached_tokens
        except AttributeError:
            # Handle cases where input_tokens_details or cached_tokens don't exist
            pass

        # Calculate cost using LiteLLM
        prompt_cost, completion_cost = cost_per_token(
            model=self.config.model_name,
            prompt_tokens=usage.input_tokens,
            completion_tokens=usage.output_tokens,
            cache_read_input_tokens=cached_tokens,
            cache_creation_input_tokens=cache_creation_tokens,
        )

        return prompt_cost + completion_cost

    def _merge_llm_and_intermediary_resources(
        self, llm_resources: list[Resource], intermediary_resources: list[Resource]
    ) -> list[Resource]:
        """
        Merge LLM-created resources with auto-tracked intermediaries.

        Strategy:
        1. Start with LLM resources (these have rich descriptions from the LLM)
        2. Fix any with sandbox paths using intermediary ground truth paths
        3. Add any intermediary resources the LLM didn't mention

        This ensures:
        - No files are lost if LLM forgets to create Resources
        - All paths are valid (using ground truth from tools)
        - LLM's descriptions are preserved when available

        Args:
            llm_resources: Resources manually created by the LLM
            intermediary_resources: Resources auto-tracked by tools (role='intermediary')

        Returns:
            Merged list of Resources with validated paths
        """
        from pathlib import Path

        logger.info(
            f"🔀 Merging resources: {len(llm_resources)} LLM + {len(intermediary_resources)} intermediary"
        )
        if intermediary_resources:
            logger.info(
                f"  Intermediary files: {[Path(r.file_path).name for r in intermediary_resources]}"
            )
        if llm_resources:
            logger.info(f"  LLM resources: {[r.name for r in llm_resources]}")

        final = []
        llm_filenames = set()

        # Pass 1: Process LLM resources, fix paths if needed
        for llm_res in llm_resources:
            if llm_res.file_path:
                filename = Path(llm_res.file_path).name
                llm_filenames.add(filename)

                # Check if path needs fixing (sandbox path or non-existent)
                if (
                    llm_res.file_path.startswith("/home/user/")
                    or not Path(llm_res.file_path).exists()
                ):
                    # Find matching intermediary with correct path
                    match = next(
                        (
                            r
                            for r in intermediary_resources
                            if Path(r.file_path).name == filename
                        ),
                        None,
                    )
                    if match:
                        # Use LLM's metadata but intermediary's path (ground truth!)
                        logger.info(
                            f"Fixed Resource path for '{llm_res.name}': "
                            f"{llm_res.file_path} → {match.file_path}"
                        )
                        final.append(
                            Resource(
                                name=llm_res.name,
                                description=llm_res.description,
                                file_path=match.file_path,  # ← Ground truth path!
                                mime_type=match.mime_type,
                                size_bytes=match.size_bytes,
                                resource_role="output",  # LLM intended this as output
                            )
                        )
                    else:
                        # No match found, keep original (will likely fail evaluation but don't break)
                        logger.warning(
                            f"Could not fix path for Resource '{llm_res.name}': "
                            f"no matching intermediary for {llm_res.file_path}"
                        )
                        final.append(llm_res)
                else:
                    # Valid path, keep as-is
                    final.append(llm_res)
            else:
                # No file_path, keep as-is (might be text-only resource)
                final.append(llm_res)

        # Pass 2: Add any intermediary resources LLM didn't mention
        for inter_res in intermediary_resources:
            filename = Path(inter_res.file_path).name
            if filename not in llm_filenames:
                # LLM forgot this file - include it with intermediary role
                logger.info(
                    f"Added forgotten intermediary resource: {inter_res.name} "
                    f"(LLM did not create a Resource for this file)"
                )
                final.append(inter_res)  # Keep role="intermediary"

        if intermediary_resources:
            logger.info(
                f"Resource merge: {len(llm_resources)} LLM resources + "
                f"{len(intermediary_resources)} intermediaries → {len(final)} final resources"
            )

        return final

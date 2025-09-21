"""
AI Agent implementation using OpenAI Agents SDK.

Provides real LLM-powered agents that can execute tasks using
system prompts and tools via the OpenAI Agents framework.
"""

import os
import time
import traceback
from typing import TYPE_CHECKING

try:
    from agents import Agent, Runner, Tool, RunResult  # type: ignore
    from agents.extensions.models.litellm_model import LitellmModel  # type: ignore
except Exception:
    Agent = None  # type: ignore
    Runner = None  # type: ignore
    Tool = None  # type: ignore
    RunResult = None  # type: ignore
    LitellmModel = None  # type: ignore
from ...config import settings
try:
    from litellm.cost_calculator import cost_per_token  # type: ignore
except Exception:  # pragma: no cover - optional dependency guard
    def cost_per_token(**kwargs):  # type: ignore
        return 0.0, 0.0

from ...schemas.core import Resource, Task
from ...schemas.workflow_agents import (
    AIAgentConfig,
    AITaskOutput,
)
from ...schemas.unified_results import ExecutionResult, create_task_result
from ..workflow_agents.interface import AgentInterface

from ..common.llm_interface import build_litellm_model_id

if TYPE_CHECKING:
    pass


from ..workflow_agents.prompts.ai_agent_prompts import (
    AI_AGENT_TASK_TEMPLATE,
    NO_RESOURCES_MESSAGE,
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
        from ..workflow_agents.tools.communication_di import COMMUNICATION_TOOLS
        from ..execution.context import AgentExecutionContext

        self.tools = tools + COMMUNICATION_TOOLS
        self.openai_agent: Agent[AgentExecutionContext] = Agent(
            model=LitellmModel(model=build_litellm_model_id(config.model_name)),
            name=config.agent_id,
            instructions=config.system_prompt,
            tools=self.tools,
            output_type=AITaskOutput,
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
            # Create execution context for dependency injection
            from ..execution.context import AgentExecutionContext

            if self.communication_service:
                context = AgentExecutionContext(
                    communication_service=self.communication_service,
                    agent_id=self.config.agent_id,
                    current_task_id=task.id,
                    tool_event_sink=self.record_tool_use_event,
                )
            else:
                # Create a minimal context if no communication service
                from ..communication.service import (
                    CommunicationService,
                )

                context = AgentExecutionContext(
                    communication_service=CommunicationService(),  # Empty service
                    agent_id=self.config.agent_id,
                    current_task_id=task.id,
                    tool_event_sink=self.record_tool_use_event,
                )

            # Prepare the task prompt
            task_prompt = self._create_task_prompt(task, resources or [])

            # Execute using OpenAI Agent with DI context
            result: RunResult = await Runner.run(
                self.openai_agent,
                task_prompt,
                context=context,  # 🎯 DI magic happens here!
            )

            # Extract structured output
            output = result.final_output
            if not isinstance(output, AITaskOutput):
                raise ValueError("Output is not an AITaskOutput")

            # Calculate execution metrics
            execution_time = time.time() - start_time
            output_resources = output.resources

            # If no resources were created, create a default one
            if not output_resources:
                output_resources.append(
                    Resource(
                        name=f"Completed: {task.name}",
                        description=f"AI agent completed task: {task.description}",
                        content=str(result),
                        content_type="text/plain",
                    )
                )

            return create_task_result(
                task_id=task.id,
                agent_id=self.config.agent_id,
                success=True,
                execution_time=execution_time,
                resources=output_resources,
                simulated_duration_hours=(execution_time / 3600.0),
                cost=self._calculate_accurate_cost(result),
                execution_notes=output.execution_notes,
                reasoning=output.reasoning,
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

    def _create_task_prompt(self, task: Task, resources: list[Resource]) -> str:
        """Create a detailed prompt for the AI agent."""

        input_resources = (
            self._format_resources(resources) if resources else NO_RESOURCES_MESSAGE
        )

        return AI_AGENT_TASK_TEMPLATE.format(
            task_name=task.name,
            task_description=task.description,
            input_resources=input_resources,
        )

    def _format_resources(self, resources: list[Resource]) -> str:
        """Format resources for inclusion in the prompt."""
        formatted = []
        for resource in resources:
            content_preview = (
                (resource.content[:200] + "...")
                if resource.content and len(resource.content) > 200
                else (resource.content or "")
            )
            formatted.append(
                f"- {resource.name}: {resource.description}\n  Content: {content_preview}"
            )
        return "\n".join(formatted)

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

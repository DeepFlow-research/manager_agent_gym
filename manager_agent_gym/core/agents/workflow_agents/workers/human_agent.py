"""
Human Mock Agent implementation with roleplay and noise simulation.

Provides faithful human worker simulation using AI roleplay with
realistic human variation, fatigue, and capability noise.
"""

import os
import random
import time
import traceback
from datetime import datetime

from agents import Agent, Runner, Tool
from agents.extensions.models.litellm_model import LitellmModel
from manager_agent_gym.config import settings

from manager_agent_gym.schemas.domain import Resource, Task
from manager_agent_gym.schemas.domain.communication import Message, MessageType
from manager_agent_gym.schemas.agents import (
    HumanAgentConfig,
    HumanWorkOutput,
    HumanTimeEstimation,
)
from manager_agent_gym.core.execution.schemas.results import (
    ExecutionResult,
    create_task_result,
)
from manager_agent_gym.core.agents.workflow_agents.common.interface import (
    AgentInterface,
)
from manager_agent_gym.core.common.llm_interface import build_litellm_model_id
from manager_agent_gym.core.common.logging import logger
from manager_agent_gym.core.agents.workflow_agents.prompts.human_agent_prompts import (
    HUMAN_SIMULATION_INSTRUCTIONS_TEMPLATE,
)
from manager_agent_gym.core.communication.service import CommunicationService
from manager_agent_gym.core.workflow.context import AgentExecutionContext


class MockHumanAgent(AgentInterface[HumanAgentConfig]):
    """
    Human mock agent that uses AI roleplay to simulate realistic human work.

    Includes noise factors like fatigue, tool availability, misunderstandings,
    and human work patterns to provide faithful simulation.
    """

    def __init__(
        self,
        config: HumanAgentConfig,
        tools: list[Tool],
    ):
        super().__init__(config)

        # Ensure OpenAI API key is available in environment
        if settings.OPENAI_API_KEY and settings.OPENAI_API_KEY != "na":
            os.environ["OPENAI_API_KEY"] = settings.OPENAI_API_KEY

        # All persona and noise configuration is now in self.config

        # Human state tracking
        self.hours_worked_today = 0.0
        self.fatigue_level = 0.0
        self.tasks_completed = 0

        # Business attributes for human agents - will be set by caller
        self.hourly_rate: float

        # Include communication tools via late import to avoid circular imports
        from manager_agent_gym.core.agents.workflow_agents.tools.communication.communication_di import (
            COMMUNICATION_TOOLS,
        )

        # Use provided tools plus communication tools
        self.private_tools = tools + COMMUNICATION_TOOLS

        # Build roleplay agent with LiteLLM model support
        roleplay_prompt = self._create_roleplay_prompt()
        self.roleplay_agent = Agent(
            name=f"{config.name}_roleplay",
            instructions=roleplay_prompt,
            model=LitellmModel(model=build_litellm_model_id(config.model_name)),
            tools=self.private_tools,
            output_type=HumanWorkOutput,
        )

        # Configuration
        self.base_hourly_rate = config.hourly_rate

    def _create_roleplay_prompt(self) -> str:
        """Create the roleplay prompt for this human persona."""

        base_prompt = self.config.generate_roleplay_prompt()

        simulation_instructions = HUMAN_SIMULATION_INSTRUCTIONS_TEMPLATE.format(
            persona_name=self.config.name,
            experience_years=self.config.experience_years,
            work_style=self.config.work_style,
            expertise_areas=", ".join(self.config.expertise_areas),
        )

        return base_prompt + simulation_instructions

    async def execute_task(
        self, task: Task, resources: list[Resource]
    ) -> ExecutionResult:
        """
        Execute a task as a human would, with realistic noise and variation.

        Args:
            task: The task to execute
            resources: Available input resources

        Returns:
            ExecutionResult with human-realistic outputs and timing
        """
        start_time = time.time()
        started_at = datetime.now()

        try:
            # Gather environmental context from messages (rubrics, alerts, etc.)
            context_messages = self._gather_context_messages()

            # Apply pre-execution noise factors
            self._update_human_state()
            current_quality_modifier = self._calculate_quality_modifier()
            speed_modifier = self._calculate_speed_modifier()

            # Check for misunderstanding
            if random.random() < self.config.misunderstanding_rate:
                return await self._handle_misunderstanding(
                    task, resources, start_time, started_at
                )

            # Execute with realistic human timing
            base_duration = await self._estimate_human_duration(task)
            simulated_duration_hours = base_duration * speed_modifier

            context = AgentExecutionContext(
                communication_service=CommunicationService()
                if not self.communication_service
                else self.communication_service,
                agent_id=self.config.agent_id,
                current_task_id=task.id,
                tool_event_sink=self.record_tool_use_event,
            )

            # Check if we should use multimodal approach
            if self.config.use_multimodal_resources and self._has_visual_resources(
                resources
            ):
                # Build multimodal input with images/PDFs/Excel
                user_message = await self._build_multimodal_human_input(
                    task, resources, current_quality_modifier, context_messages
                )

                # Execute using roleplay agent with multimodal content
                result = await Runner.run(
                    self.roleplay_agent, [user_message], context=context
                )
            else:
                # Fallback to text-only approach (backward compatible)
                task_prompt = self._create_human_task_prompt(
                    task, resources, current_quality_modifier, context_messages
                )

                # Execute using roleplay agent with DI context
                result = await Runner.run(
                    self.roleplay_agent, task_prompt, context=context
                )

            # Extract structured output
            output = result.final_output
            if not isinstance(output, HumanWorkOutput):
                raise ValueError("Output is not a HumanWorkOutput")

            # Calculate final metrics
            execution_time = time.time() - start_time

            # Create output resources
            output_resources = output.resources
            if not output_resources:
                raise ValueError("No resources generated by human agent")

            # Calculate cost
            actual_cost = simulated_duration_hours * self.base_hourly_rate

            # Update human state
            self.hours_worked_today += simulated_duration_hours
            self.tasks_completed += 1

            # Extract execution trace if enabled
            execution_trace = None
            if self.config.enable_execution_tracing:
                try:
                    from manager_agent_gym.core.agents.workflow_agents.utils.trace_extractor import (
                        extract_execution_trace,
                    )

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

            return create_task_result(
                task_id=task.id,
                agent_id=self.config.agent_id,
                success=True,
                resources=output_resources,
                execution_time=execution_time,
                cost=actual_cost,
                execution_trace=execution_trace,
                simulated_duration_hours=simulated_duration_hours,
                execution_notes=self._create_execution_notes(
                    output, current_quality_modifier
                ),
                reasoning=output.work_process,
            )

        except Exception as e:
            logger.error(f"Human agent task execution failed: {traceback.format_exc()}")
            raise e

    def _update_human_state(self):
        """Update human state factors like fatigue."""
        self.fatigue_level = min(
            self.hours_worked_today * self.config.fatigue_rate,
            0.5,  # max fatigue penalty
        )

    def _calculate_quality_modifier(self) -> float:
        """Calculate current quality modifier based on human state."""
        base_quality = random.gauss(
            self.config.base_quality_mean,
            0.1,  # quality std dev
        )

        # Apply fatigue penalty
        base_quality -= self.fatigue_level

        return max(0.0, min(1.0, base_quality))

    def _calculate_speed_modifier(self) -> float:
        """Calculate speed modifier for this execution."""
        return max(
            0.1,
            random.gauss(
                1.0,  # task completion speed multiplier mean
                0.2,  # task completion speed multiplier std
            ),
        )

    async def _estimate_human_duration(
        self, task: Task, default_duration: float = 1.0
    ) -> float:
        """Estimate realistic human duration for a task using LLM reasoning."""
        if task.estimated_duration_hours:
            return task.estimated_duration_hours

        try:
            # Create a time estimation agent with human perspective
            time_estimation_agent = Agent(
                model=LitellmModel(
                    model=build_litellm_model_id(self.config.model_name)
                ),
                name=f"{self.config.name}_time_estimator",
                instructions=f"""
                You are {self.config.role} with {self.config.experience_years} years of experience.
                                
                Your task is to estimate how long it would take YOU SPECIFICALLY to complete the given task.
                Consider:
                - Your background: {self.config.background}
                - Your expertise areas: {", ".join(self.config.expertise_areas)}
                - Your work style: {self.config.work_style}
                - Your personality traits: {", ".join(self.config.personality_traits)}
                - Realistic time for research, planning, execution, and review
                - Potential challenges you might face given your background

                Be realistic - include time for breaks, getting up to speed, and potential obstacles.
                Don't just estimate the "ideal" time, but the real time it would take you personally.""",
                output_type=HumanTimeEstimation,
            )

            # Get time estimation from LLM
            result = await Runner.run(
                time_estimation_agent,
                f"""Task: {task.description}

                Please estimate how many hours this task would take you to complete, considering your specific background and experience level.

                Provide your reasoning and estimated hours.
            """,
            )

            time_estimation: HumanTimeEstimation = result.final_output

            # Use the LLM's estimated hours
            return max(0.1, time_estimation.estimated_hours)  # Minimum 0.1 hours

        except Exception:
            logger.error(
                f"Human agent time estimation failed: {traceback.format_exc()}"
            )
            return default_duration

    async def _handle_misunderstanding(
        self,
        task: Task,
        resources: list[Resource],
        start_time: float,
        started_at: datetime,
    ) -> ExecutionResult:
        """Handle case where human misunderstands the task via an LLM roleplay run."""
        # Estimate duration for costing
        human_duration = await self._estimate_human_duration(task)

        # Create execution context for DI tools (same as normal path)
        from manager_agent_gym.core.workflow.context import AgentExecutionContext

        if self.communication_service:
            context = AgentExecutionContext(
                communication_service=self.communication_service,
                agent_id=self.config.agent_id,
                current_task_id=task.id,
            )
        else:
            from manager_agent_gym.core.communication.service import (
                CommunicationService,
            )

            context = AgentExecutionContext(
                communication_service=CommunicationService(),
                agent_id=self.config.agent_id,
                current_task_id=task.id,
            )

        # Build misunderstanding-oriented prompt and run the roleplay agent
        # Check if we should use multimodal approach
        if self.config.use_multimodal_resources and self._has_visual_resources(
            resources
        ):
            # Build multimodal misunderstood input
            user_message = await self._build_multimodal_misunderstood_input(
                task, resources
            )
            result = await Runner.run(
                self.roleplay_agent, [user_message], context=context
            )
        else:
            # Text-only fallback
            task_prompt = self._create_misunderstood_task_prompt(task, resources)
            result = await Runner.run(self.roleplay_agent, task_prompt, context=context)

        output = result.final_output
        if not isinstance(output, HumanWorkOutput):
            raise ValueError("Output is not a HumanWorkOutput")

        output_resources = output.resources
        if not output_resources:
            raise ValueError(
                "No resources generated by human agent (misunderstanding path)"
            )

        execution_time = time.time() - start_time

        return create_task_result(
            task_id=task.id,
            agent_id=self.config.agent_id,
            success=True,  # Human believes they executed correctly
            resources=output_resources,
            execution_time=execution_time,
            cost=human_duration * self.base_hourly_rate,
            simulated_duration_hours=human_duration,
            execution_notes=[
                "Task execution under a subtle misunderstanding of requirements",
                "Output may be misaligned with the original intent",
            ],
            reasoning=output.work_process,
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
        """Format rubric messages into evaluation criteria section for human perspective.

        Args:
            messages: List of rubric update messages

        Returns:
            Formatted evaluation criteria section for the prompt template
        """
        if not messages:
            return ""

        rubric_text = "### Manager's Quality Expectations\n\n"
        rubric_text += (
            "Your manager has communicated specific quality criteria for this work:\n\n"
        )

        for msg in messages:
            pref_name = msg.metadata.get("preference_name", "Quality Standard")
            rubric_text += f"**{pref_name}:**\n{msg.content}\n\n"

        rubric_text += "*Make sure your work addresses these criteria. If anything is unclear, note it in your output.*"

        return rubric_text

    def _create_human_task_prompt(
        self,
        task: Task,
        resources: list[Resource],
        quality_modifier: float,
        context_messages: dict[str, list[Message]] | None = None,
    ) -> str:
        """Create a task prompt from the human's perspective.

        Args:
            task: The task to execute
            resources: Available input resources
            quality_modifier: Current quality level
            context_messages: Optional context from messages (rubrics, etc.)

        Returns:
            Formatted task prompt
        """
        from manager_agent_gym.core.agents.workflow_agents.prompts.human_agent_prompts import (
            HUMAN_TASK_ASSIGNMENT_TEMPLATE,
        )

        resources_text = (
            self._format_resources(resources)
            if resources
            else "No specific resources provided"
        )

        # Build evaluation criteria section
        evaluation_criteria = ""
        if context_messages and context_messages.get("rubrics"):
            evaluation_criteria = self._format_rubric_messages(
                context_messages["rubrics"]
            )

        # Use template with all sections
        task_prompt = HUMAN_TASK_ASSIGNMENT_TEMPLATE.format(
            persona_name=self.config.name,
            task_name=task.name,
            task_description=task.description,
            resources_list=resources_text,
            time_constraints="",
            dependencies="",
            evaluation_criteria=evaluation_criteria,
        )

        # Add context about current state
        state_context = ""
        if quality_modifier < 0.7:
            state_context = "\n*Note: You're feeling a bit tired/stressed today - be mindful of this as you work.*\n"
        elif quality_modifier > 0.9:
            state_context = "\n*Note: You're feeling sharp and focused today - great conditions for quality work.*\n"

        # Add expertise reminder
        expertise_note = f"""
### Your Background
- **Expertise**: {", ".join(self.config.expertise_areas)}
- **Work Style**: {self.config.work_style}
- **Experience**: {self.config.experience_years} years

Use these strengths as you approach this work. Take breaks as needed and work at a sustainable pace.
"""

        return f"{task_prompt}\n{state_context}\n{expertise_note}"

    def _create_misunderstood_task_prompt(
        self, task: Task, resources: list[Resource]
    ) -> str:
        """Create a task prompt that simulates a subtle, plausible misunderstanding."""
        from manager_agent_gym.core.agents.workflow_agents.prompts.human_agent_prompts import (
            HUMAN_TASK_ASSIGNMENT_TEMPLATE,
        )

        resources_text = (
            self._format_resources(resources)
            if resources
            else "No specific resources provided"
        )

        base_prompt = HUMAN_TASK_ASSIGNMENT_TEMPLATE.format(
            persona_name=self.config.name,
            task_name=task.name,
            task_description=task.description,
            resources_list=resources_text,
            time_constraints="",
            dependencies="",
        )

        return f"""{base_prompt}

Important twist: You slightly misunderstand the task in a realistic, plausible way a human might.
- Pick one reasonable misinterpretation (e.g., focusing on format over substance, optimizing the wrong KPI, solving a related-but-different problem, or assuming a different audience).
- Proceed confidently without flagging confusion. Do not state that you misunderstood.
- Produce a complete work product consistent with that misunderstanding.
- Demonstrate craftsmanship appropriate to your background and work style.

Deliver the output as you normally would for this task, fully believing it satisfies the request.
"""

    def _create_execution_notes(
        self, output: HumanWorkOutput, quality_modifier: float
    ) -> list[str]:
        """Create execution notes from human work output."""
        notes = [
            f"Human worker: {self.config.name}",
            f"Work style: {self.config.work_style}",
            f"Experience: {self.config.experience_years} years",
            f"Current fatigue level: {self.fatigue_level:.2f}",
            f"Quality modifier applied: {quality_modifier:.2f}",
        ]

        notes.extend(output.challenges_encountered)
        return notes

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

    async def _build_multimodal_human_input(
        self,
        task: Task,
        resources: list[Resource],
        quality_modifier: float,
        context_messages: dict[str, list[Message]] | None = None,
    ):
        """Build multimodal input for human agent with images/PDFs/Excel.

        Args:
            task: The task to execute
            resources: Available input resources
            quality_modifier: Current quality level
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

        # Build evaluation criteria section
        evaluation_criteria = ""
        if context_messages and context_messages.get("rubrics"):
            evaluation_criteria = self._format_rubric_messages(
                context_messages["rubrics"]
            )

        # Build task text using human template style
        task_text = f"### Task Assignment for {self.config.name}\n\n"
        task_text += f"**Task:** {task.name}\n\n"
        task_text += f"**Description:**\n{task.description}\n\n"

        if evaluation_criteria:
            task_text += evaluation_criteria + "\n\n"

        task_text += "**Resources Available:**\n"

        # Add context about current state
        if quality_modifier < 0.7:
            task_text += "\n*Note: You're feeling a bit tired/stressed today - be mindful of this as you work.*\n\n"
        elif quality_modifier > 0.9:
            task_text += "\n*Note: You're feeling sharp and focused today - great conditions for quality work.*\n\n"

        # Get resource content blocks (images, PDFs, Excel, text)
        resource_blocks = await processor.format_resources_as_content(
            resources,
            include_metadata=True,
        )

        # Add expertise reminder at the end
        expertise_note = "\n\n### Your Background\n"
        expertise_note += f"- **Expertise**: {', '.join(self.config.expertise_areas)}\n"
        expertise_note += f"- **Work Style**: {self.config.work_style}\n"
        expertise_note += f"- **Experience**: {self.config.experience_years} years\n\n"
        expertise_note += "Use these strengths as you approach this work. Take breaks as needed and work at a sustainable pace."

        # Combine task text with resource blocks
        return create_user_message(
            create_text_content(task_text),
            *resource_blocks,
            create_text_content(expertise_note),
        )

    async def _build_multimodal_misunderstood_input(
        self,
        task: Task,
        resources: list[Resource],
    ):
        """Build multimodal input for misunderstanding scenario.

        Args:
            task: The task to execute
            resources: Available input resources

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

        # Build task text
        task_text = f"### Task Assignment for {self.config.name}\n\n"
        task_text += f"**Task:** {task.name}\n\n"
        task_text += f"**Description:**\n{task.description}\n\n"
        task_text += "**Resources Available:**\n"

        # Get resource content blocks
        resource_blocks = await processor.format_resources_as_content(
            resources,
            include_metadata=True,
        )

        # Add misunderstanding instruction
        misunderstanding_note = "\n\nImportant twist: You slightly misunderstand the task in a realistic, plausible way a human might.\n"
        misunderstanding_note += "- Pick one reasonable misinterpretation (e.g., focusing on format over substance, optimizing the wrong KPI, solving a related-but-different problem, or assuming a different audience).\n"
        misunderstanding_note += "- Proceed confidently without flagging confusion. Do not state that you misunderstood.\n"
        misunderstanding_note += (
            "- Produce a complete work product consistent with that misunderstanding.\n"
        )
        misunderstanding_note += "- Demonstrate craftsmanship appropriate to your background and work style.\n\n"
        misunderstanding_note += "Deliver the output as you normally would for this task, fully believing it satisfies the request."

        # Combine
        return create_user_message(
            create_text_content(task_text),
            *resource_blocks,
            create_text_content(misunderstanding_note),
        )

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

            # Add format-specific metadata if available (format as key=value)
            if resource.file_format_metadata:
                metadata_items = [
                    f"{k}={v}" for k, v in resource.file_format_metadata.items()
                ]
                resource_info.append(f"  Metadata: {', '.join(metadata_items)}")

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
        return "\n".join(formatted)

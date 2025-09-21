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
from ...config import settings

from ...schemas.core import Resource, Task
from ...schemas.workflow_agents import (
    HumanAgentConfig,
    HumanWorkOutput,
    HumanTimeEstimation,
)
from ...schemas.unified_results import ExecutionResult, create_task_result
from ..workflow_agents.interface import AgentInterface
from ..common.llm_interface import build_litellm_model_id
from ..common.logging import logger
from ..workflow_agents.prompts.human_agent_prompts import (
    HUMAN_SIMULATION_INSTRUCTIONS_TEMPLATE,
)


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
        from ..workflow_agents.tools.communication_di import COMMUNICATION_TOOLS

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
            # Apply pre-execution noise factors
            self._update_human_state()
            current_quality_modifier = self._calculate_quality_modifier()
            speed_modifier = self._calculate_speed_modifier()

            # Check for misunderstanding
            if random.random() < self.config.misunderstanding_rate:
                return await self._handle_misunderstanding(
                    task, resources, start_time, started_at
                )

            # Create human-realistic task prompt
            task_prompt = self._create_human_task_prompt(
                task, resources, current_quality_modifier
            )

            # Execute with realistic human timing
            base_duration = await self._estimate_human_duration(task)
            simulated_duration_hours = base_duration * speed_modifier

            # Create execution context for DI tools
            from ..execution.context import AgentExecutionContext

            if self.communication_service:
                context = AgentExecutionContext(
                    communication_service=self.communication_service,
                    agent_id=self.config.agent_id,
                    current_task_id=task.id,
                    tool_event_sink=self.record_tool_use_event,
                )
            else:
                from ..communication.service import CommunicationService

                context = AgentExecutionContext(
                    communication_service=CommunicationService(),
                    agent_id=self.config.agent_id,
                    current_task_id=task.id,
                    tool_event_sink=self.record_tool_use_event,
                )

            # Execute using roleplay agent with DI context
            result = await Runner.run(self.roleplay_agent, task_prompt, context=context)

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

            return create_task_result(
                task_id=task.id,
                agent_id=self.config.agent_id,
                success=True,
                resources=output_resources,
                execution_time=execution_time,
                cost=actual_cost,
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
        from ..execution.context import AgentExecutionContext

        if self.communication_service:
            context = AgentExecutionContext(
                communication_service=self.communication_service,
                agent_id=self.config.agent_id,
                current_task_id=task.id,
            )
        else:
            from ..communication.service import CommunicationService

            context = AgentExecutionContext(
                communication_service=CommunicationService(),
                agent_id=self.config.agent_id,
                current_task_id=task.id,
            )

        # Build misunderstanding-oriented prompt and run the roleplay agent
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

    def _create_human_task_prompt(
        self, task: Task, resources: list[Resource], quality_modifier: float
    ) -> str:
        """Create a task prompt from the human's perspective."""
        from ..workflow_agents.prompts.human_agent_prompts import (
            HUMAN_TASK_ASSIGNMENT_TEMPLATE,
        )

        quality_context = ""
        if quality_modifier < 0.7:
            quality_context = "\n(Note: You're feeling a bit tired/stressed today)"
        elif quality_modifier > 0.9:
            quality_context = "\n(Note: You're feeling sharp and focused today)"

        resources_text = (
            self._format_resources(resources)
            if resources
            else "No specific resources provided"
        )

        # Use template but keep the existing quality modifier logic
        base_prompt = HUMAN_TASK_ASSIGNMENT_TEMPLATE.format(
            persona_name=self.config.name,
            task_name=task.name,
            task_description=task.description,
            resources_list=resources_text,
            time_constraints="",
            dependencies="",
        )

        # Add quality context and work style guidance
        return f"""{base_prompt}

{quality_context}

Please complete this task using your expertise in {", ".join(self.config.expertise_areas)}. 
Apply your {self.config.work_style} work style and {self.config.experience_years} years of experience.

Work through this step-by-step as you naturally would, using your available tools and taking breaks as needed.
"""

    def _create_misunderstood_task_prompt(
        self, task: Task, resources: list[Resource]
    ) -> str:
        """Create a task prompt that simulates a subtle, plausible misunderstanding."""
        from ..workflow_agents.prompts.human_agent_prompts import (
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

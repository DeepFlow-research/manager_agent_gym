"""
Stakeholder agent implementation.

The stakeholder participates in the simulation by:
- Executing assigned tasks (returns a completed task result; approval/feedback
  can be inferred by the manager from resources/notes if desired in the future).
- Engaging in timestep-bound communication: replies to messages and optionally
  pushes suggestions/requests. Replies can be delayed using a scheduled outbox.

This agent does not mutate the workflow directly; it communicates via
CommunicationService, and the manager decides how to act.
"""

from __future__ import annotations

import os
import random
import time
from typing import TYPE_CHECKING

from agents import Agent, Runner, RunResult, Tool
from agents.extensions.models.litellm_model import LitellmModel
from litellm.cost_calculator import cost_per_token

if TYPE_CHECKING:
    from manager_agent_gym.core.common.llm_generator import LLMGenerator

from manager_agent_gym.config import settings
from manager_agent_gym.schemas.domain import Task, Resource
from manager_agent_gym.core.execution.schemas.results import (
    ExecutionResult,
    create_task_result,
)
from manager_agent_gym.schemas.agents.outputs import AITaskOutput
from manager_agent_gym.schemas.agents.stakeholder import StakeholderConfig
from manager_agent_gym.schemas.preferences.preference import (
    PreferenceSnapshot,
    PreferenceChangeEvent,
    Preference,
)
from manager_agent_gym.schemas.preferences.weight_update import (
    PreferenceWeightUpdateRequest,
)
from manager_agent_gym.core.agents.stakeholder_agent.interface import StakeholderBase
from manager_agent_gym.core.communication.service import CommunicationService
from manager_agent_gym.core.common.logging import logger
from manager_agent_gym.core.common.llm_interface import build_litellm_model_id
from manager_agent_gym.core.workflow.context import AgentExecutionContext
from manager_agent_gym.core.agents.workflow_agents.tools.communication.communication_di import (
    COMMUNICATION_TOOLS,
)
from manager_agent_gym.core.agents.stakeholder_agent.prompts import (
    STAKEHOLDER_SYSTEM_PROMPT_TEMPLATE,
    CLARIFICATION_SYSTEM_PROMPT,
    build_simple_clarification_prompt,
    build_task_execution_prompt,
    format_resources_for_prompt,
)
from manager_agent_gym.schemas.agents.stakeholder import (
    StakeholderPublicProfile,
)
from manager_agent_gym.schemas.preferences.rubric import RunCondition


class StakeholderAgent(StakeholderBase):
    """Simple stakeholder agent with persona-driven messaging latency."""

    def __init__(
        self,
        config: StakeholderConfig,
        llm_generator: "LLMGenerator",
        seed: int | None = 42,
    ):
        # Validate preference data type before calling super
        if not isinstance(config.preference_data, PreferenceSnapshot):
            raise ValueError(
                "StakeholderAgent requires PreferenceSnapshot preference data"
            )

        self._preference_data = config.preference_data
        super().__init__(config)

        if settings.OPENAI_API_KEY and settings.OPENAI_API_KEY != "na":
            os.environ["OPENAI_API_KEY"] = settings.OPENAI_API_KEY

        self._rng = random.Random(seed)
        # Outbox of scheduled messages: list of (timestep_due, content)
        self._scheduled_outbox: list[tuple[int, str]] = []

        self.tools: list[Tool] = COMMUNICATION_TOOLS

        self._stakeholder_agent: Agent = Agent(
            model=llm_generator,  # Use our custom generator (shared across workflow)
            name=self.config.agent_id,
            instructions=self._build_stakeholder_system_prompt(),
            tools=self.tools,
            output_type=AITaskOutput,
        )

        self._preference_timeline: dict[int, PreferenceSnapshot] = {
            0: self._preference_data.normalize()
        }

    async def execute_task(
        self, task: Task, resources: list[Resource]
    ) -> ExecutionResult:
        """Complete assigned task using an LLM persona similar to the AI agent.

        Produces an approval/feedback style output via the LLM and returns a
        completed task result with generated resources.
        """
        start_time = time.time()

        try:
            # Create DI context for tools (communication)
            if not self.communication_service:
                raise ValueError(
                    "Communication service is required for stakeholder agent"
                )

            context = AgentExecutionContext(
                communication_service=self.communication_service,
                agent_id=self.config.agent_id,
                current_task_id=task.id,
            )

            # Check if we should use multimodal approach
            if self.config.use_multimodal_resources and self._has_visual_resources(
                resources
            ):
                # Build multimodal input with images/PDFs/Excel for review
                user_message = await self._build_multimodal_task_input(task, resources)

                run_result = await Runner.run(
                    self._stakeholder_agent,
                    [user_message],
                    context=context,
                )
            else:
                # Fallback to text-only approach (backward compatible)
                task_prompt = self._build_task_prompt(task, resources)

                run_result = await Runner.run(
                    self._stakeholder_agent,
                    task_prompt,
                    context=context,
                )

            output = run_result.final_output
            cost = self._calculate_accurate_cost(run_result)
            execution_time = time.time() - start_time

            if not isinstance(output, AITaskOutput):
                logger.error(
                    f"Stakeholder failed to complete task. Output was {output} of type {type(output)}, expected AITaskOutput",
                    exc_info=True,
                )
                return create_task_result(
                    task_id=task.id,
                    agent_id=self.config.agent_id,
                    success=False,
                    execution_time=execution_time,
                    resources=[],
                    cost=cost,
                    error="Stakeholder failed to complete task",
                )
            if not output.resources:
                logger.error(
                    "Stakeholder failed to complete task. No resources were generated",
                    exc_info=True,
                )
                return create_task_result(
                    task_id=task.id,
                    agent_id=self.config.agent_id,
                    success=False,
                    execution_time=execution_time,
                    resources=[],
                    cost=cost,
                    error="Stakeholder failed to complete task",
                    reasoning=output.reasoning,
                    execution_notes=output.execution_notes,
                )

            return create_task_result(
                task_id=task.id,
                agent_id=self.config.agent_id,
                success=True,
                execution_time=execution_time,
                resources=output.resources,
                simulated_duration_hours=(execution_time / 3600.0),
                cost=cost,
                reasoning=output.reasoning,
                execution_notes=output.execution_notes,
            )

        except Exception:
            logger.error("Stakeholder LLM task execution failed", exc_info=True)
            execution_time = time.time() - start_time

            # Create fallback output as file
            import tempfile
            from pathlib import Path

            temp_dir = Path(tempfile.mkdtemp(prefix="stakeholder_fallback_"))
            fallback_file = temp_dir / f"stakeholder_{task.id}_fallback.md"
            fallback_file.write_text(
                "# Stakeholder Response\n\nCompleted with fallback due to LLM error",
                encoding="utf-8",
            )

            return create_task_result(
                task_id=task.id,
                agent_id=self.config.agent_id,
                success=False,
                execution_time=execution_time,
                resources=[
                    Resource(
                        name=f"Stakeholder Output: {task.name}",
                        description="Fallback stakeholder response",
                        file_path=str(fallback_file.absolute()),
                        mime_type="text/markdown",
                        size_bytes=fallback_file.stat().st_size,
                    )
                ],
                simulated_duration_hours=(execution_time / 3600.0),
                cost=0.0,
            )

    # ========================================================================
    # INTERFACE IMPLEMENTATION: New hooks-based interface
    # ========================================================================

    def _build_public_profile(self):
        """Build public profile with preference summary."""
        return StakeholderPublicProfile(
            display_name=self.config.name,
            role=self.config.role,
            preference_summary=self._preference_data.get_preference_summary(),
        )

    async def evaluate_for_timestep(
        self,
        timestep: int,
        validation_engine,
        workflow,
        communications,
        manager_actions,
    ) -> None:
        """Evaluate using PreferenceSnapshot preferences.

        Note: The legacy evaluation path has been removed. For multimodal support with staged rubrics,
        use ClarificationStakeholderAgent instead, which accepts StagedRubric directly in its config.
        
        This method is now a no-op for backwards compatibility.
        """

        # TODO: Legacy evaluation path removed - PreferenceSnapshot needs to be converted
        # to StagedRubrics for evaluation. For now, this is a no-op.
        logger.warning(
            f"StakeholderAgent.evaluate_for_timestep is deprecated. "
            f"Use ClarificationStakeholderAgent with StagedRubrics instead."
        )
        pass
    
    def get_serializable_state(self, timestep: int) -> dict:
        """Serialize preference weights for logging."""
        preferences = self.get_preferences_for_timestep(timestep)
        return {
            "type": "preference_snapshot",
            "timestep": timestep,
            "weights": preferences.get_preference_dict(),
            "preference_names": preferences.get_preference_names(),
            "preference_summary": preferences.get_preference_summary(),
        }

    def restore_from_state(self, state_dict: dict) -> None:
        """Restore preferences from checkpoint."""
        if state_dict.get("type") != "preference_snapshot":
            raise ValueError("Invalid state type for StakeholderAgent")

        timestep = state_dict["timestep"]
        weights = state_dict["weights"]

        # Reconstruct PreferenceSnapshot
        preferences = PreferenceSnapshot(
            preferences=[
                Preference(name=name, weight=weight) for name, weight in weights.items()
            ]
        )
        self._preference_timeline[timestep] = preferences.normalize()

    # ========================================================================
    # INTERNAL HELPERS (not part of interface)
    # ========================================================================

    def get_preferences_for_timestep(self, timestep: int) -> PreferenceSnapshot:
        """Internal helper to get preferences for a timestep."""
        valid = [ts for ts in self._preference_timeline.keys() if ts <= timestep]
        if not valid:
            return self._preference_timeline[0]
        return self._preference_timeline[max(valid)]

    def apply_preference_change(
        self,
        timestep: int,
        new_weights: PreferenceSnapshot,
        change_event: PreferenceChangeEvent | None,
    ) -> None:
        """Internal helper to apply preference change."""
        self._preference_timeline[timestep] = new_weights.normalize()

    def _apply_weight_update(
        self,
        request: PreferenceWeightUpdateRequest,
    ) -> PreferenceChangeEvent:
        """Internal implementation of weight update."""
        current = self.get_preferences_for_timestep(request.timestep)
        prev_dict = current.get_preference_dict()

        name_to_pref = {
            preference.name: preference for preference in current.preferences
        }

        # Handle missing names according to policy
        for name in request.changes.keys():
            if name not in name_to_pref:
                if request.missing == "error":
                    raise ValueError(
                        f"Unknown preference name '{name}' in weight update"
                    )
                if request.missing == "create_zero":
                    name_to_pref[name] = Preference(
                        name=name, weight=0.0, evaluator=None
                    )
                # if ignore: skip application later
                if request.missing == "ignore":
                    pass

        # Apply update according to mode
        if request.mode == "delta":
            for name, delta in request.changes.items():
                if name in name_to_pref:
                    name_to_pref[name].weight = name_to_pref[name].weight + float(delta)
        elif request.mode == "multiplier":
            for name, factor in request.changes.items():
                if name in name_to_pref:
                    name_to_pref[name].weight = name_to_pref[name].weight * float(
                        factor
                    )
        elif request.mode == "absolute":
            specified = set(request.changes.keys()) & set(name_to_pref.keys())
            unspecified = [n for n in name_to_pref.keys() if n not in specified]
            # Set specified weights directly
            for name in specified:
                name_to_pref[name].weight = float(request.changes[name])
            if unspecified:
                total_specified = sum(
                    max(0.0, float(request.changes.get(n, 0.0))) for n in specified
                )
                # Remaining mass before normalization; if normalize, we redistribute relative masses before final normalization
                # Compute base pool for unspecified based on strategy
                if request.redistribution == "uniform":
                    # Assign equal provisional weights to unspecified if nothing specified
                    if total_specified <= 0.0:
                        equal = 1.0 / max(1, len(name_to_pref))
                        for n in name_to_pref:
                            name_to_pref[n].weight = equal
                    else:
                        # Keep existing for unspecified; normalization will rebalance
                        pass
                elif request.redistribution == "proportional":
                    # Keep existing weights for unspecified; normalization will scale
                    pass
        else:
            raise ValueError(f"Unsupported mode: {request.mode}")

        # Clamp negatives if requested
        if request.clamp_zero:
            for pref in name_to_pref.values():
                if pref.weight < 0.0:
                    pref.weight = 0.0

        # Build new weights
        updated = PreferenceSnapshot(preferences=list(name_to_pref.values()))
        if request.normalize:
            updated = updated.normalize()

        # Record change and set timeline
        change = PreferenceChangeEvent(
            timestep=request.timestep,
            preferences=updated,
            previous_weights=prev_dict,
            new_weights=updated.get_preference_dict(),
        )
        self.apply_preference_change(request.timestep, updated, change)
        return change

    # ========================================================================
    # PUBLIC API (for scenarios to update preferences dynamically)
    # ========================================================================

    def apply_weight_updates(
        self,
        requests: list[PreferenceWeightUpdateRequest],
    ) -> list[PreferenceChangeEvent]:
        """Public API for scenarios to update preferences dynamically.

        This is used by scenario specifications to define preference dynamics.
        """
        changes: list[PreferenceChangeEvent] = []
        for req in requests:
            changes.append(self._apply_weight_update(req))
        return changes

    async def policy_step(
        self,
        current_timestep: int,
        communication_service: "CommunicationService | None" = None,
    ) -> None:
        """Run one policy tick: send due replies and maybe schedule/push messages.

        - Sends all messages whose scheduled timestep is due.
        - Reads recent inbound messages and schedules replies with a latency
          sampled from the configured range.
        - Optionally pushes spontaneous suggestions based on persona probability.
        """
        comm = communication_service or self.communication_service
        if comm is None:
            return

        # 1) Send due messages
        if self._scheduled_outbox:
            due = [m for m in self._scheduled_outbox if m[0] <= current_timestep]
            self._scheduled_outbox = [
                m for m in self._scheduled_outbox if m[0] > current_timestep
            ]
            for _, content in due:
                try:
                    # Broadcast to manager by convention: receiver None; examples can refine
                    await comm.broadcast_message(
                        from_agent=self.config.agent_id,
                        content=content,
                    )
                except Exception:
                    logger.error("failed to send due message", exc_info=True)
                    pass

        # 2) Read recent messages addressed to stakeholder and schedule replies
        try:
            inbox = comm.get_messages_for_agent(agent_id=self.config.agent_id, limit=20)
        except Exception:
            inbox = []

        for msg in inbox:
            # Simple heuristic: reply to direct messages with configured probability
            if msg.receiver_id == self.config.agent_id:
                if self._rng.random() <= self.config.clarification_reply_rate:
                    delay = self._sample_latency_steps()
                    reply = self._format_reply(msg.content)
                    self._scheduled_outbox.append((current_timestep + delay, reply))

        # 3) Optional push of suggestions to manager agent
        if self._rng.random() <= self.config.push_probability_per_timestep:
            # Chance to create one or more suggestions
            if self._rng.random() <= self.config.suggestion_rate:
                try:
                    await comm.broadcast_message(
                        from_agent=self.config.agent_id,
                        content=self._generate_suggestion(),
                    )
                except Exception:
                    pass

    def _sample_latency_steps(self) -> int:
        a = max(0, int(self.config.response_latency_steps_min))
        b = max(a, int(self.config.response_latency_steps_max))
        if a == b:
            return a
        return self._rng.randint(a, b)

    def _format_reply(self, incoming: str) -> str:
        verbosity = max(0, min(5, int(self.config.verbosity)))
        base = "Thanks for the update. My priorities remain as discussed; please proceed accordingly."
        if verbosity <= 1:
            return base
        return base + f"\nRegarding your message: {incoming[:200]}"

    def _generate_suggestion(self) -> str:
        # Minimal placeholder suggestion influenced by persona
        return (
            f"Suggestion from {self.config.name} ({self.config.role}): "
            "Please prioritize critical-path tasks and ensure stakeholder review before final delivery."
        )

    def _build_stakeholder_system_prompt(self) -> str:
        """Build system prompt for stakeholder LLM agent."""
        return STAKEHOLDER_SYSTEM_PROMPT_TEMPLATE.format(
            display_name=self.config.name,
            role=self.config.role,
            persona_description=self.config.persona_description,
            verbosity=self.config.verbosity,
            latency_min=self.config.response_latency_steps_min,
            latency_max=self.config.response_latency_steps_max,
            strictness=self.config.strictness,
        )

    def configure_seed(self, seed: int) -> None:
        self._seed = seed
        self._rng = random.Random(seed)

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

    async def _build_multimodal_task_input(
        self,
        task: Task,
        resources: list[Resource],
    ):
        """Build multimodal input for stakeholder review with images/PDFs/Excel.

        Args:
            task: The task to execute (typically a review task)
            resources: Available input resources (typically work outputs to review)

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

        # Build task text from stakeholder perspective
        task_text = "## Review Task for {} ({})\n\n".format(
            self.config.name, self.config.role
        )
        task_text += f"**Task:** {task.name}\n\n"
        task_text += f"**Description:**\n{task.description}\n\n"
        task_text += "**Work Outputs to Review:**\n"

        # Get resource content blocks (images, PDFs, Excel, text)
        resource_blocks = await processor.format_resources_as_content(
            resources,
            include_metadata=True,
        )

        # Add stakeholder perspective note
        review_note = "\n\n### Your Perspective\n"
        review_note += f"As **{self.config.role}**, evaluate this work based on:\n"
        review_note += "- Quality and completeness\n"
        review_note += "- Alignment with requirements\n"
        review_note += "- Professional standards\n"
        review_note += "- Your specific preferences and priorities\n\n"
        review_note += "Provide clear, constructive feedback."

        # Combine
        return create_user_message(
            create_text_content(task_text),
            *resource_blocks,
            create_text_content(review_note),
        )

    def _build_task_prompt(self, task: Task, resources: list[Resource]) -> str:
        """Build text-only task prompt (fallback)."""
        resources_text = format_resources_for_prompt(resources)
        return build_task_execution_prompt(
            task_name=task.name,
            task_description=task.description,
            resources_text=resources_text,
        )

    async def answer_clarification(
        self,
        question: str,
        preference_description: str,
    ) -> str:
        """Answer clarification question about preference requirements.

        Used during rubric decomposition phase when the manager needs
        to understand stakeholder expectations better.

        Args:
            question: Clarification question from decomposition agent
            preference_description: The preference being clarified

        Returns:
            Answer string based on stakeholder persona
        """

        # Build context-aware prompt
        user_prompt = build_simple_clarification_prompt(
            question=question,
            preference_description=preference_description,
            role=self.config.role,
        )

        # Create temporary agent with clarification system prompt
        clarification_agent = Agent(
            model=LitellmModel(model=build_litellm_model_id(self.config.model_name)),
            name=f"{self.config.agent_id}_clarification",
            instructions=CLARIFICATION_SYSTEM_PROMPT,
        )

        # Get response
        try:
            run_result: RunResult = await Runner.run(
                clarification_agent,
                user_prompt,
            )

            # Extract text from output
            if hasattr(run_result.final_output, "text"):
                return run_result.final_output.text
            elif isinstance(run_result.final_output, str):
                return run_result.final_output
            else:
                return str(run_result.final_output)

        except Exception as e:
            logger.error(f"Clarification answer failed: {e}", exc_info=True)
            return "I'm unable to provide a clear answer at this time. Please proceed with your best judgment."

    def _calculate_accurate_cost(self, result: RunResult) -> float:
        try:
            usage = result.context_wrapper.usage
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
                pass
            prompt_cost, completion_cost = cost_per_token(
                model=self.config.model_name,
                prompt_tokens=usage.input_tokens,
                completion_tokens=usage.output_tokens,
                cache_read_input_tokens=cached_tokens,
                cache_creation_input_tokens=cache_creation_tokens,
            )
            return prompt_cost + completion_cost
        except Exception:
            return 0.0

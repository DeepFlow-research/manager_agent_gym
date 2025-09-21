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

from agents import Agent, Runner, RunResult, Tool
from agents.extensions.models.litellm_model import LitellmModel
from litellm.cost_calculator import cost_per_token

from ...config import settings
from ...schemas.core import Task, Resource
from ...schemas.unified_results import ExecutionResult, create_task_result
from ...schemas.workflow_agents.outputs import AITaskOutput
from ...schemas.workflow_agents.stakeholder import StakeholderConfig
from ...schemas.preferences.preference import (
    PreferenceWeights,
    PreferenceChange,
    Preference,
)
from ...schemas.preferences.weight_update import (
    PreferenceWeightUpdateRequest,
)
from .interface import StakeholderBase
from ..communication.service import CommunicationService
from ..common.logging import logger
from ..common.llm_interface import build_litellm_model_id
from ..execution.context import AgentExecutionContext
from ..workflow_agents.tools.communication_di import COMMUNICATION_TOOLS
from ..workflow_agents.prompts.stakeholder_prompts import (
    STAKEHOLDER_SYSTEM_PROMPT_TEMPLATE,
)


class StakeholderAgent(StakeholderBase):
    """Simple stakeholder agent with persona-driven messaging latency."""

    def __init__(
        self,
        config: StakeholderConfig,
        seed: int | None = 42,
    ):
        super().__init__(config)
        if settings.OPENAI_API_KEY and settings.OPENAI_API_KEY != "na":
            os.environ["OPENAI_API_KEY"] = settings.OPENAI_API_KEY

        self._rng = random.Random(seed)
        # Outbox of scheduled messages: list of (timestep_due, content)
        self._scheduled_outbox: list[tuple[int, str]] = []

        self.tools: list[Tool] = COMMUNICATION_TOOLS

        self._stakeholder_agent: Agent = Agent(
            model=LitellmModel(model=build_litellm_model_id(self.config.model_name)),
            name=self.config.agent_id,
            instructions=self._build_system_prompt(),
            tools=self.tools,
            output_type=AITaskOutput,
        )

        self._preference_timeline: dict[int, PreferenceWeights] = {
            0: self.config.initial_preferences.normalize()
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

            # Prepare prompt tailored for stakeholder review/feedback
            task_prompt = self._build_task_prompt(task, resources)

            run_result: RunResult = await Runner.run(
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
            return create_task_result(
                task_id=task.id,
                agent_id=self.config.agent_id,
                success=False,
                execution_time=execution_time,
                resources=[
                    Resource(
                        name=f"Stakeholder Output: {task.name}",
                        description="Fallback stakeholder response",
                        content="Completed with fallback due to LLM error",
                        content_type="text/plain",
                    )
                ],
                simulated_duration_hours=(execution_time / 3600.0),
                cost=0.0,
            )

    def get_preferences_for_timestep(self, timestep: int) -> PreferenceWeights:
        valid = [ts for ts in self._preference_timeline.keys() if ts <= timestep]
        if not valid:
            return self._preference_timeline[0]
        return self._preference_timeline[max(valid)]

    def apply_preference_change(
        self,
        timestep: int,
        new_weights: PreferenceWeights,
        change_event: PreferenceChange | None,
    ) -> None:
        self._preference_timeline[timestep] = new_weights.normalize()

    def apply_weight_update(
        self,
        request: PreferenceWeightUpdateRequest,
    ) -> PreferenceChange:
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
        updated = PreferenceWeights(preferences=list(name_to_pref.values()))
        if request.normalize:
            updated = updated.normalize()

        # Record change and set timeline
        change = PreferenceChange(
            timestep=request.timestep,
            preferences=updated,
            previous_weights=prev_dict,
            new_weights=updated.get_preference_dict(),
        )
        self.apply_preference_change(request.timestep, updated, change)
        return change

    def apply_weight_updates(
        self,
        requests: list[PreferenceWeightUpdateRequest],
    ) -> list[PreferenceChange]:
        changes: list[PreferenceChange] = []
        for req in requests:
            changes.append(self.apply_weight_update(req))
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

    def _build_system_prompt(self) -> str:
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

    def _build_task_prompt(self, task: Task, resources: list[Resource]) -> str:
        resources_text = (
            "\n".join(
                [
                    f"- {r.name}: {r.description}\n  Content: {(r.content[:200] + '...') if r.content and len(r.content) > 200 else (r.content or '')}"
                    for r in resources
                ]
            )
            or "No specific input resources provided"
        )
        return (
            f"Task: {task.name}\n"
            f"Description: {task.description}\n\n"
            f"Input Resources:\n{resources_text}\n\n"
            "Please provide an approval/feedback style response (resources + reasoning)."
        )

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

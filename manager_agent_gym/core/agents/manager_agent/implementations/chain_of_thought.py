"""
Chain of Thought Manager Agent using constrained LLM generation.

This manager agent uses direct LiteLLM calls with Pydantic schema constraints
to ensure reliable, validated actions. Based on the management.py pattern.
"""

import traceback
from datetime import datetime


from manager_agent_gym.core.agents.manager_agent.common.interface import ManagerAgent
from manager_agent_gym.core.agents.manager_agent.prompts.structured_manager_prompts import (
    STRUCTURED_MANAGER_SYSTEM_PROMPT_TEMPLATE,
)
from manager_agent_gym.core.agents.manager_agent.common.action_constraints import (
    build_context_constrained_action_schema,
)

from manager_agent_gym.core.agents.manager_agent.common.llm_action_utils import (
    get_action_descriptions,
    get_default_action_classes,
)
from manager_agent_gym.schemas.domain.workflow import Workflow
from manager_agent_gym.schemas.manager import ManagerObservation
from manager_agent_gym.core.execution.schemas.state import ExecutionState
from manager_agent_gym.schemas.agents.stakeholder import (
    StakeholderPublicProfile,
)
from manager_agent_gym.core.agents.manager_agent.actions import (
    BaseManagerAction,
    FailedAction,
)
from manager_agent_gym.schemas.preferences.preference import PreferenceSnapshot
from manager_agent_gym.core.common.logging import logger
from manager_agent_gym.core.common.llm_interface import (
    generate_structured_response,
    LLMInferenceTruncationError,
)
from manager_agent_gym.schemas.agents.base import AgentConfig


class ChainOfThoughtManagerAgent(ManagerAgent):
    """
    Manager agent that uses constrained LLM generation for reliable actions.

    This agent:
    - Uses direct LiteLLM calls with structured output
    - Validates all actions through the action registry
    - Provides clean error handling and logging
    - Follows the management.py pattern for reliability
    """

    def __init__(
        self,
        preferences: PreferenceSnapshot | None = None,
        model_name: str = "o3",
        action_classes: list[type[BaseManagerAction]] | None = None,
        manager_persona: str = "Strategic Project Manager",
    ):
        super().__init__("structured_manager", preferences)
        self.model_name = model_name
        self.action_classes = action_classes or get_default_action_classes()
        self.manager_persona = manager_persona

    async def take_action(self, observation: ManagerObservation) -> BaseManagerAction:
        """
        Take an action based on workflow observation using constrained generation.

        Args:
            observation: Current workflow state

        Returns:
            Validated BaseManagerAction

        Raises:
            ValueError: If LLM generates invalid action
        """
        try:
            # Build constrained schema for LLM using current valid IDs
            constrained_schema = build_context_constrained_action_schema(
                self.action_classes, observation
            )
            # Prepare context using prompt templates
            system_prompt = self._get_system_prompt(
                observation.available_agent_metadata
            )
            user_prompt = self._prepare_context(observation)

            # Direct LLM call with structured output (validated by Pydantic)
            parsed_action = await generate_structured_response(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                response_type=constrained_schema,
                model=self.model_name,
                seed=self._seed,
            )
            return parsed_action.action  # type: ignore[attr-defined]

        except LLMInferenceTruncationError as e:
            concise_reason = (
                (e.provider_fields.get("refusal_text") or "").strip()
                or (e.provider_fields.get("finish_reason") or "").strip()
                or "provider refusal"
            )
            failed_action = FailedAction(
                reasoning=f"Provider refusal: {concise_reason}. Observing without action this step.",
                metadata={
                    "refusal_text": e.refusal_text,
                    "finish_reason": e.finish_reason,
                },
                success=False,
                result_summary=f"Provider refusal: {concise_reason}. Observing without action this step.",
            )
            logger.warning(
                "LLM refusal when generating manager action; falling back to FailedAction: %s",
                str(e),
            )
            return failed_action

        except Exception as e:
            logger.error(f"Structured manager failed: {traceback.format_exc()}")
            return FailedAction(
                reasoning=f"Structured manager failed to take action: {traceback.format_exc()}",
                metadata={"error": str(e)},
                success=False,
                result_summary=f"Structured manager failed to take action: {traceback.format_exc()}",
            )

    async def step(
        self,
        workflow: Workflow,
        execution_state: ExecutionState,
        stakeholder_profile: StakeholderPublicProfile | None = None,
        current_timestep: int = 0,
        running_tasks: dict | None = None,
        completed_task_ids: set | None = None,
        failed_task_ids: set | None = None,
        communication_service=None,
        previous_reward: float = 0.0,
        done: bool = False,
    ) -> BaseManagerAction:
        observation = await self.create_observation(
            workflow=workflow,
            execution_state=execution_state,
            current_timestep=current_timestep,
            running_tasks=running_tasks,
            completed_task_ids=completed_task_ids,
            failed_task_ids=failed_task_ids,
            communication_service=communication_service,
        )
        return await self.take_action(observation)

    def reset(self) -> None:
        """Reset manager state (structured manager is stateless)."""

        pass

    def _get_system_prompt(self, available_agent_metadata: list[AgentConfig]) -> str:
        """Get the system prompt for the manager agent using templates."""
        action_descriptions = get_action_descriptions(self.action_classes)
        formatted_actions = self._format_actions(action_descriptions)

        return STRUCTURED_MANAGER_SYSTEM_PROMPT_TEMPLATE.format(
            today_date=datetime.now().strftime("%d.%m.%Y"),
            available_actions=formatted_actions,
            available_agents="\n".join(
                [
                    f"{i + 1}. {agent.get_agent_capability_summary()}"
                    for i, agent in enumerate(available_agent_metadata)
                ]
            ),
        )

    def _prepare_context(self, observation: ManagerObservation) -> str:
        """Prepare comprehensive, ID-focused workflow context for the LLM.

        The context should expose:
        - Key execution metrics and progress
        - Valid IDs for actions (ready tasks, available agents)
        - Brief summaries of constraints, messages, and recent manager actions
        - A short, actionable decision aid aligned with the system prompt
        """

        # Basic counts
        ready_count = len(observation.ready_task_ids)
        running_count = len(observation.running_task_ids)
        completed_count = len(observation.completed_task_ids)
        failed_count = len(observation.failed_task_ids)
        available_count = len(observation.available_agent_metadata)

        total_tracked = ready_count + running_count + completed_count + failed_count
        completion_rate = (
            (completed_count / total_tracked * 100) if total_tracked > 0 else 0.0
        )
        utilization_rate = (
            (
                (ready_count + running_count)
                / (ready_count + running_count + available_count)
                * 100
            )
            if (ready_count + running_count + available_count) > 0
            else 0.0
        )

        # Helpful ID previews (limited to keep prompts compact)
        preview_n = 10
        ready_ids_preview = [
            str(x) for x in list(observation.ready_task_ids)[: preview_n * 2]
        ]
        running_ids_preview = [
            str(x) for x in list(observation.running_task_ids)[: preview_n * 2]
        ]
        completed_ids_preview = [
            str(x) for x in list(observation.completed_task_ids)[: preview_n * 2]
        ]
        failed_ids_preview = [
            str(x) for x in list(observation.failed_task_ids)[: preview_n * 2]
        ]

        # Serialize constraints compactly with key details (name, type, enforcement, applicability, brief description)
        constraint_lines: list[str] = []
        for c in observation.constraints[:preview_n]:
            try:
                applies_to = (
                    ", ".join(c.applicable_task_types[:5])
                    if c.applicable_task_types
                    else "all"
                )
                desc = c.description or ""
                desc_preview = (desc[:120] + "…") if len(desc) > 120 else desc

                line = f"- {c.name} [{c.constraint_type}, enforce={c.enforcement_level}] | applies: {applies_to}"
                if desc_preview:
                    line += f" | {desc_preview}"
                constraint_lines.append(line)
            except Exception:
                constraint_lines.append("- <unavailable constraint>")
        constraints_block = (
            "\n".join(constraint_lines) if constraint_lines else "(none)"
        )

        # Recent messages summary (sender → receiver | type: content…)
        message_lines: list[str] = []
        for m in observation.recent_messages[:preview_n]:
            try:
                content_preview = (
                    (m.content[:140] + "…") if len(m.content) > 140 else m.content
                )
                message_lines.append(
                    f"- {m.sender_id} → {m.receiver_id or 'ALL'} | {m.message_type}: {content_preview}"
                )
            except Exception:
                message_lines.append("- <unable to render message>")
        messages_block = (
            "\n".join(message_lines) if message_lines else "(no recent messages)"
        )

        # Recent manager actions (briefs)
        action_lines: list[str] = []
        for a in self.get_action_buffer(preview_n):
            try:
                reason_preview = (
                    (a.summary[:120] + "…")
                    if a.summary and len(a.summary) > 120
                    else (a.summary or "")
                )
                action_lines.append(
                    f"- t={a.timestep}: {a.action_type}{' — Result: ' + reason_preview if reason_preview else ''}"
                )
            except Exception:
                action_lines.append("- <unable to render action brief>")
        actions_block = (
            "\n".join(action_lines) if action_lines else "(no prior manager actions)"
        )

        # Valid ID universes (helps the model avoid fabricating IDs)
        id_guidance_lines = [
            f"- all_task_ids (count={len(observation.task_ids)}): sample={[str(x) for x in observation.task_ids[:preview_n]]}",
            f"- all_agent_ids (count={len(observation.agent_ids)}): sample={observation.agent_ids[:preview_n]}",
            f"- all_resource_ids (count={len(observation.resource_ids)}): sample={[str(x) for x in observation.resource_ids[:preview_n]]}",
        ]

        # Stakeholder profile (public data only)
        stakeholder_block = (
            observation.stakeholder_profile.model_dump_json(indent=2)
            if observation.stakeholder_profile
            else "(no stakeholder profile available)"
        )

        # Time awareness strings
        time_budget_line = ""
        if observation.max_timesteps is not None:
            time_budget_line = "There is a maximum number of timesteps for this workflow before it is ended by force by the stakeholder."
            time_budget_line = (
                f"- time_budget: {observation.timestep}/{observation.max_timesteps}"
            )
        time_remaining_line = ""
        if observation.timesteps_remaining is not None:
            time_remaining_line = (
                f" | timesteps_remaining: {observation.timesteps_remaining}"
            )
        time_progress_line = ""
        if observation.time_progress is not None:
            time_progress_line = f" | time_progress: {observation.time_progress:.1%}"

        return f"""
### Execution Snapshot (timestep {observation.timestep})
- workflow_id: {observation.workflow_id}

- current_workflow_summary: {observation.workflow_summary}

- execution_state: {observation.execution_state}
- progress: {observation.workflow_progress:.1%}
{time_budget_line}{time_remaining_line}{time_progress_line}

### Task Status Counts
- ready: {ready_count} | running: {running_count} | completed: {completed_count} | failed: {failed_count}

### ID Universes
{id_guidance_lines}

### Performance Indicators
- completion_rate: {completion_rate:.1f}% of tracked
- resource_utilization: {utilization_rate:.1f}%

### Actionable ID Previews
- ready_task_ids (sample): {ready_ids_preview}
- running_task_ids (sample): {running_ids_preview}
- completed_task_ids (sample): {completed_ids_preview}
- failed_task_ids (sample): {failed_ids_preview}

### Constraints (sample)
{constraints_block}

### Recent Communications (sample)
{messages_block}

### Manager Action History (recent)
{actions_block}

### Stakeholder Profile (public)
{stakeholder_block}
"""

    def _format_actions(self, action_descriptions: dict[str, str]) -> str:
        """Format action descriptions for the system prompt."""
        formatted = []
        for action_type, description in action_descriptions.items():
            formatted.append(f"- **{action_type}**: {description}")

        return "\n".join(formatted)

    def _format_priorities(self, action_priorities: list[str]) -> str:
        """Format action priorities for the system prompt."""
        formatted = []
        action_descriptions = get_action_descriptions(self.action_classes)
        for i, action_type in enumerate(action_priorities, 1):
            description = action_descriptions[action_type]
            formatted.append(f"{i}. **{action_type}**: {description}")
        return "\n".join(formatted)

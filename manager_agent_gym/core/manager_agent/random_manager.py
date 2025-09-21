"""
Simple baseline manager agents for faster testing:
- RandomManagerAgent: chooses a random valid action each step
- RandomManagerAgentV2: RNG chooses one allowed action type, then an LLM
  generates the structured output for that single action (constrained)
- OneShotDelegateManagerAgent: assigns all pending tasks once, then no-ops
"""

import random
import asyncio
import traceback
from datetime import datetime

from .interface import ManagerAgent
from ...schemas.execution import ManagerObservation
from ...schemas.execution.manager_actions import (
    BaseManagerAction,
    FailedAction,
    NoOpAction,
    AssignTaskAction,
    GetWorkflowStatusAction,
    GetAvailableAgentsAction,
    GetPendingTasksAction,
    AssignAllPendingTasksAction,
    AssignTasksToAgentsAction,
    AssignmentPair,
)
from .action_constraints import build_context_constrained_action_schema
from ...schemas.core.workflow import Workflow
from ...schemas.execution.state import ExecutionState
from ...schemas.preferences.preference import PreferenceWeights
from .llm_action_utils import (
    get_action_descriptions,
    get_default_action_classes,
)
from .prompts.structured_manager_prompts import (
    STRUCTURED_MANAGER_SYSTEM_PROMPT_TEMPLATE,
)
from ..common.llm_interface import generate_structured_response
from ..common.logging import logger
from ...core.workflow_agents.interface import AgentConfig
from ...schemas.workflow_agents.stakeholder import StakeholderPublicProfile


class BulkAssignmentPromptBuilder:
    """Helper to build prompts for bulk task->agent assignment.

    Uses the manager observation's workflow summary and available agent configs
    to produce a concise, informative prompt for a single-shot LLM mapping.
    """

    @staticmethod
    def build_system_prompt() -> str:
        return (
            "You are a workflow orchestration manager operating on a task DAG.\n"
            "Goal: assign each task to the best-fit agent so work can proceed without further input.\n"
            "Respect constraints and practical roles: prefer AI agents for analysis/automation;\n"
            "route approvals, governance, and sign-offs to human/stakeholder roles when required.\n"
            "Maximize overall workflow throughput and quality; avoid leaving tasks unassigned.\n"
            "Output exactly one AssignTasksToAgentsAction with a complete 'assignments' list.\n"
        )

    @staticmethod
    def build_user_prompt(
        workflow_summary: str, available_agent_configs: list[AgentConfig]
    ) -> str:
        agents_block = "\n".join(
            [cfg.get_agent_capability_summary() for cfg in available_agent_configs]
        )
        return (
            "## WORKFLOW\n"
            f"{workflow_summary}\n\n"
            "## AVAILABLE AGENTS\n"
            f"{agents_block}\n\n"
            "## INSTRUCTIONS\n"
            "- Provide a complete mapping: include every task_id you can see in the workflow.\n"
            "- Choose the best agent per task based on capabilities and role suitability.\n"
            "- If uncertain, choose the most capable non-stakeholder agent; avoid stakeholder for execution unless clearly required.\n"
        )


class RandomManagerAgent(ManagerAgent):
    """Baseline: randomly chooses among a small set of safe actions."""

    def __init__(self, preferences: PreferenceWeights, seed: int = 42):
        super().__init__(agent_id="random_manager", preferences=preferences)
        self.random = random.Random(seed)

    def configure_seed(self, seed: int) -> None:
        self._seed = seed
        self.random = random.Random(seed)

    async def take_action(self, observation: ManagerObservation) -> BaseManagerAction:
        await asyncio.sleep(0.5)
        candidates: list[BaseManagerAction] = [
            NoOpAction(
                reasoning="Random baseline: choose to do nothing",
                success=True,
                result_summary="idle",
            ),
            GetWorkflowStatusAction(
                reasoning="Random baseline: get status",
                success=True,
                result_summary="status",
            ),
            GetAvailableAgentsAction(
                reasoning="Random baseline: inspect agents",
                success=True,
                result_summary="agents",
            ),
            GetPendingTasksAction(
                reasoning="Random baseline: inspect pending",
                success=True,
                result_summary="pending",
            ),
        ]

        # If we have both a ready task and an available agent, include assignment
        if observation.ready_task_ids and observation.available_agent_metadata:
            candidates.append(
                AssignTaskAction(
                    reasoning="Random baseline: assign a ready task",
                    task_id=str(self.random.choice(observation.ready_task_ids)),
                    agent_id=self.random.choice(
                        observation.available_agent_metadata
                    ).agent_id,
                    success=True,
                    result_summary="assigned first ready task",
                )
            )

        return self.random.choice(candidates)

    def reset(self) -> None:
        pass

    async def step(
        self,
        workflow: Workflow,
        execution_state: ExecutionState,
        stakeholder_profile: StakeholderPublicProfile,
        current_timestep: int,
        running_tasks: dict,
        completed_task_ids: set,
        failed_task_ids: set,
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
            stakeholder_profile=stakeholder_profile,
        )
        return await self.take_action(observation)


class RandomManagerAgentV2(ManagerAgent):
    """Random action selection with constrained LLM structuring.

    This variant RNG-selects a single allowed action type, then uses constrained
    LLM generation (schema-limited to only that action) to produce the structured
    action payload with reasoning, mirroring the ChainOfThoughtManagerAgent flow
    but restricting the action set to exactly one randomly chosen action.
    """

    def __init__(
        self,
        preferences: PreferenceWeights,
        model_name: str = "o3",
        allowed_action_classes: list[type[BaseManagerAction]] | None = None,
        seed: int = 42,
    ):
        super().__init__(agent_id="random_manager_v2", preferences=preferences)
        self.model_name = model_name
        self.allowed_action_classes = (
            allowed_action_classes or get_default_action_classes()
        )
        self.random = random.Random(seed)

    def configure_seed(self, seed: int) -> None:
        self._seed = seed
        self.random = random.Random(seed)

    async def take_action(self, observation: ManagerObservation) -> BaseManagerAction:
        try:
            # Narrow the candidate action classes minimally based on feasibility
            candidate_classes = self._get_candidate_action_classes(observation)
            selected_class = self.random.choice(candidate_classes)

            # Constrain LLM to only the selected action class with valid IDs
            constrained_schema = build_context_constrained_action_schema(
                [selected_class], observation
            )

            system_prompt = self._get_system_prompt(
                [selected_class], observation.available_agent_metadata
            )
            user_prompt = self._prepare_context(observation, selected_class)

            parsed_action = await generate_structured_response(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                response_type=constrained_schema,
                model=self.model_name,
                seed=self._seed,
            )

            return parsed_action.action  # type: ignore[attr-defined]

        except Exception:
            logger.error(
                f"RandomManagerAgentV2 failed to generate action: {traceback.format_exc()}"
            )
            return FailedAction(
                reasoning="Fallback: failed to generate structured action this step",
                success=False,
                result_summary="failed to generate structured action this step",
                metadata={},
            )

    def reset(self) -> None:
        pass

    async def step(
        self,
        workflow: Workflow,
        execution_state: ExecutionState,
        stakeholder_profile: StakeholderPublicProfile,
        current_timestep: int,
        running_tasks: dict,
        completed_task_ids: set,
        failed_task_ids: set,
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
            stakeholder_profile=stakeholder_profile,
        )
        return await self.take_action(observation)

    def _get_candidate_action_classes(
        self, observation: ManagerObservation
    ) -> list[type[BaseManagerAction]]:
        """Return a minimally filtered list of action classes for RNG selection."""
        candidates = list(self.allowed_action_classes)

        # If assignment is impossible this step, avoid selecting AssignTaskAction
        if (
            not observation.ready_task_ids or not observation.available_agent_metadata
        ) and AssignTaskAction in candidates:
            candidates = [c for c in candidates if c is not AssignTaskAction]

        # Always ensure at least a safe introspection action remains
        safe_defaults = {
            GetWorkflowStatusAction,
            GetAvailableAgentsAction,
            GetPendingTasksAction,
            NoOpAction,
        }
        if not any(c in candidates for c in safe_defaults):
            candidates.append(GetWorkflowStatusAction)

        return candidates

    def _get_system_prompt(
        self,
        selected_action_classes: list[type[BaseManagerAction]],
        available_agent_configs: list[AgentConfig],
    ) -> str:
        """Build a system prompt that lists only the selected action."""
        descriptions = get_action_descriptions(selected_action_classes)
        formatted_actions = "\n".join(
            [f"- **{k}**: {v}" for k, v in descriptions.items()]
        )
        return STRUCTURED_MANAGER_SYSTEM_PROMPT_TEMPLATE.format(
            today_date=datetime.now().strftime("%d.%m.%Y"),
            available_actions=formatted_actions,
            available_agents="\n".join(
                [
                    agent.get_agent_capability_summary()
                    for agent in available_agent_configs
                ]
            ),
        )

    def _prepare_context(
        self,
        observation: ManagerObservation,
        selected_class: type[BaseManagerAction],
    ) -> str:
        """Prepare a concise context and explicitly state the pre-selected action type."""

        ready_count = len(observation.ready_task_ids)
        running_count = len(observation.running_task_ids)
        completed_count = len(observation.completed_task_ids)
        available_count = len(observation.available_agent_metadata)

        try:
            field_info = selected_class.model_fields["action_type"]  # type: ignore[attr-defined,index]
            action_type_name = (
                field_info.default
                if field_info and field_info.default is not None
                else selected_class.__name__
            )
        except Exception:
            action_type_name = selected_class.__name__

        # Provide concrete IDs to support parameter completion when applicable
        details_lines: list[str] = []
        ready_ids = [str(x) for x in observation.ready_task_ids]
        running_ids = [str(x) for x in observation.running_task_ids]
        completed_ids = [str(x) for x in observation.completed_task_ids]
        available_agents = [x.agent_id for x in observation.available_agent_metadata]

        if ready_ids:
            details_lines.append(f"- Ready task IDs: {ready_ids}")
        if running_ids:
            details_lines.append(f"- Running task IDs: {running_ids}")
        if completed_ids:
            details_lines.append(f"- Completed task IDs: {completed_ids}")
        if available_agents:
            details_lines.append(f"- Available agent IDs: {available_agents}")

        details_block = "\n".join(details_lines)

        return (
            f"## INSTRUCTIONS\n"
            f"  - Provide 'reasoning' explaining why the chosen action is reasonable now.\n"
            f"- Then provide the 'action' object with all required parameters for '{action_type_name}'.\n"
            f"- Do not propose any other action types.\n"
            f"## PRE-SELECTED ACTION TYPE\n"
            f"You MUST output exactly one action of type '{action_type_name}'.\n\n"
            f"## OBSERVATION (timestep {observation.timestep})\n"
            f"- Ready tasks: {ready_count}\n"
            f"- Running tasks: {running_count}\n"
            f"- Completed tasks: {completed_count}\n"
            f"- Available agents: {available_count}\n"
            f"{(details_block) if details_block else ''}\n\n"
        )


class OneShotDelegateManagerAgent(ManagerAgent):
    """Baseline: delegate all pending tasks to any agent exactly once, then no-op."""

    def __init__(self, preferences: PreferenceWeights, model_name: str = "o3"):
        super().__init__(agent_id="oneshot_delegate_manager", preferences=preferences)
        self._has_delegated = False
        self.model_name = model_name

    async def take_action(self, observation: ManagerObservation) -> BaseManagerAction:
        await asyncio.sleep(0.5)
        if self._has_delegated:
            return NoOpAction(
                reasoning="One-shot delegate: no further actions",
                success=True,
                result_summary="No action taken, already delegated all pending tasks",
            )

        # Fallback agent preference (non-stakeholder if possible)
        fallback_agent = None
        avail = observation.available_agent_metadata
        if avail:
            non_stakeholders = [a for a in avail if a.agent_type != "stakeholder"]
            fallback_agent = non_stakeholders[0] if non_stakeholders else avail[0]

        # Attempt LLM-generated bulk mapping
        try:
            constrained_schema = build_context_constrained_action_schema(
                [AssignTasksToAgentsAction], observation
            )

            system_prompt = BulkAssignmentPromptBuilder.build_system_prompt()
            user_prompt = BulkAssignmentPromptBuilder.build_user_prompt(
                workflow_summary=observation.workflow_summary,
                available_agent_configs=(avail or []),
            )

            parsed = await generate_structured_response(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                response_type=constrained_schema,
                model=self.model_name,
                seed=self._seed,
            )

            action: AssignTasksToAgentsAction = parsed.action  # type: ignore[attr-defined]

            # Fill gaps with fallback agent
            have = {pair.task_id for pair in action.assignments}
            for tid in observation.task_ids:
                if tid not in have and fallback_agent is not None:
                    action.assignments.append(
                        AssignmentPair(task_id=tid, agent_id=fallback_agent.agent_id)
                    )

            self._has_delegated = True
            action.reasoning = "Bulk LLM mapping with fallback for unassigned tasks"
            action.success = True
            action.result_summary = "Applied bulk task->agent mapping (with fallback)"
            return action

        except Exception:
            logger.error("One-shot bulk assignment failed; falling back", exc_info=True)
            self._has_delegated = True
            return AssignAllPendingTasksAction(
                reasoning="Fallback: delegated all pending tasks to a single agent",
                agent_id=fallback_agent.agent_id if fallback_agent else None,
                success=True,
                result_summary="delegated all pending tasks (fallback)",
            )

    def reset(self) -> None:
        self._has_delegated = False

    async def step(
        self,
        workflow: Workflow,
        execution_state: ExecutionState,
        stakeholder_profile: StakeholderPublicProfile,
        current_timestep: int,
        running_tasks: dict,
        completed_task_ids: set,
        failed_task_ids: set,
        communication_service=None,
        previous_reward: float = 0.0,
        done: bool = False,
    ) -> BaseManagerAction:
        observation = await self.create_observation(
            workflow=workflow,
            execution_state=execution_state,
            stakeholder_profile=stakeholder_profile,
            current_timestep=current_timestep,
            running_tasks=running_tasks,
            completed_task_ids=completed_task_ids,
            failed_task_ids=failed_task_ids,
            communication_service=communication_service,
        )
        return await self.take_action(observation)

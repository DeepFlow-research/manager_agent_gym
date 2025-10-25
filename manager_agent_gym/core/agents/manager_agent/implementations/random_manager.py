import random
import asyncio
import traceback
from datetime import datetime
from typing import TYPE_CHECKING

from manager_agent_gym.core.agents.manager_agent.common.interface import ManagerAgent
from manager_agent_gym.schemas.manager import ManagerObservation
from manager_agent_gym.core.agents.manager_agent.actions import (
    BaseManagerAction,
    FailedAction,
    NoOpAction,
    AssignTaskAction,
    GetWorkflowStatusAction,
    GetAvailableAgentsAction,
    GetPendingTasksAction,
)
from manager_agent_gym.core.agents.manager_agent.common.action_constraints import (
    build_context_constrained_action_schema,
)
from manager_agent_gym.schemas.domain.workflow import Workflow
from manager_agent_gym.core.execution.schemas.state import ExecutionState
from manager_agent_gym.schemas.preferences.preference import PreferenceSnapshot
from manager_agent_gym.core.agents.manager_agent.common.llm_action_utils import (
    get_action_descriptions,
    get_default_action_classes,
)
from manager_agent_gym.core.agents.manager_agent.prompts.structured_manager_prompts import (
    STRUCTURED_MANAGER_SYSTEM_PROMPT_TEMPLATE,
)
from manager_agent_gym.core.common.logging import logger
from manager_agent_gym.core.agents.workflow_agents.common.interface import AgentConfig
from manager_agent_gym.schemas.agents.stakeholder import (
    StakeholderPublicProfile,
)

if TYPE_CHECKING:
    from manager_agent_gym.core.common.llm_generator import LLMGenerator


class RandomManagerAgent(ManagerAgent):
    """Baseline: randomly chooses among a small set of safe actions."""

    def __init__(self, preferences: PreferenceSnapshot, seed: int = 42):
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


class RandomManagerAgentV2(ManagerAgent):
    """Random action selection with constrained LLM structuring.

    This variant RNG-selects a single allowed action type, then uses constrained
    LLM generation (schema-limited to only that action) to produce the structured
    action payload with reasoning, mirroring the ChainOfThoughtManagerAgent flow
    but restricting the action set to exactly one randomly chosen action.
    """

    def __init__(
        self,
        preferences: PreferenceSnapshot,
        llm_generator: "LLMGenerator",
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
        self.llm_generator = llm_generator

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

            # Use Agents SDK approach
            from agents import Agent
            from agents.run import Runner

            agent = Agent(
                name="random_manager",
                model=self.llm_generator,
                instructions=system_prompt,
                output_type=constrained_schema,
            )

            agent_result = await Runner.run(agent, user_prompt)
            parsed_action = agent_result.final_output

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

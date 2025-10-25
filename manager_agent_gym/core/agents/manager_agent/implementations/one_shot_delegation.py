import asyncio
from typing import TYPE_CHECKING

from manager_agent_gym.core.agents.manager_agent.common.interface import ManagerAgent
from manager_agent_gym.schemas.manager import ManagerObservation
from manager_agent_gym.core.agents.manager_agent.actions import (
    BaseManagerAction,
    NoOpAction,
    AssignAllPendingTasksAction,
    AssignTasksToAgentsAction,
    AssignmentPair,
)
from manager_agent_gym.core.agents.manager_agent.common.action_constraints import (
    build_context_constrained_action_schema,
)
from manager_agent_gym.schemas.domain.workflow import Workflow
from manager_agent_gym.core.execution.schemas.state import ExecutionState
from manager_agent_gym.schemas.preferences.preference import PreferenceSnapshot
from manager_agent_gym.core.common.logging import logger
from manager_agent_gym.core.agents.workflow_agents.common.interface import AgentConfig
from manager_agent_gym.schemas.agents.stakeholder import (
    StakeholderPublicProfile,
)

if TYPE_CHECKING:
    from manager_agent_gym.core.common.llm_generator import LLMGenerator


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


class OneShotDelegateManagerAgent(ManagerAgent):
    """Baseline: delegate all pending tasks to any agent exactly once, then no-op."""

    def __init__(
        self,
        preferences: PreferenceSnapshot,
        llm_generator: "LLMGenerator",
        model_name: str = "o3",
    ):
        super().__init__(agent_id="oneshot_delegate_manager", preferences=preferences)
        self._has_delegated = False
        self.model_name = model_name
        self.llm_generator = llm_generator

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
        else:
            non_stakeholders = []

        # Attempt LLM-generated bulk mapping
        try:
            constrained_schema = build_context_constrained_action_schema(
                [AssignTasksToAgentsAction], observation
            )

            system_prompt = BulkAssignmentPromptBuilder.build_system_prompt()
            user_prompt = BulkAssignmentPromptBuilder.build_user_prompt(
                workflow_summary=observation.workflow_summary,
                available_agent_configs=(non_stakeholders or []),
            )

            # Use Agents SDK approach
            from agents import Agent
            from agents.run import Runner

            agent = Agent(
                name="oneshot_delegator",
                model=self.llm_generator,
                instructions=system_prompt,
                output_type=constrained_schema,
            )

            agent_result = await Runner.run(agent, user_prompt)
            parsed = agent_result.final_output

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
            stakeholder_profile=stakeholder_profile,
            current_timestep=current_timestep,
            running_tasks=running_tasks,
            completed_task_ids=completed_task_ids,
            failed_task_ids=failed_task_ids,
            communication_service=communication_service,
        )
        return await self.take_action(observation)

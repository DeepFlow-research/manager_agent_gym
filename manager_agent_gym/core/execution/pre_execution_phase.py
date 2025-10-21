from datetime import datetime
from typing import TYPE_CHECKING

from manager_agent_gym.core.execution.schemas.pre_execution import PreExecutionLog
from manager_agent_gym.core.common.logging import logger
from manager_agent_gym.core.agents.manager_agent.actions import (
    GeneratePreferenceRubricAction,
)
from manager_agent_gym.core.execution.schemas.state import ExecutionState


from manager_agent_gym.core.execution.schemas.pre_execution import (
    ClarificationTurn,
)
from manager_agent_gym.core.workflow.phases.interface import PreExecutionPhase
from manager_agent_gym.core.agents.manager_agent.implementations.rubric_generation_manager.rubric_generation import (
    ManagerAgentGeneratedRubric,
)

if TYPE_CHECKING:
    from manager_agent_gym.schemas.domain.workflow import Workflow
    from manager_agent_gym.core.communication.service import CommunicationService
    from manager_agent_gym.core.agents.manager_agent.implementations.rubric_generation_manager.rubric_decomposition_manager import (
        RubricDecompositionManagerAgent,
    )
    from manager_agent_gym.core.agents.stakeholder_agent.rubric_stakeholder import (
        ClarificationStakeholderAgent,
    )


class InitialRubricGenerationPhase(PreExecutionPhase):
    """Orchestrates clarification dialogue for rubric generation.

    Runs communication loop between manager and stakeholder until rubrics
    are generated or max turns reached.

    TODO: Implement proper completion detection by comparing rubrics_generated
    against expected preferences count from workflow metadata instead of just
    checking len(rubrics_generated) > 0.
    """

    def __init__(
        self,
        manager: "RubricDecompositionManagerAgent",
        stakeholder: "ClarificationStakeholderAgent",
        communication_service: "CommunicationService",
        max_turns: int = 3,
    ):
        """Initialize pre-execution phase runner.

        Args:
            manager: Rubric decomposition manager agent
            stakeholder: Clarification stakeholder agent
            communication_service: Communication service for message passing
            max_turns: Maximum dialogue turns allowed
        """
        self.manager = manager
        self.stakeholder = stakeholder
        self.comm = communication_service
        self.max_turns = max_turns

        self.manager.set_communication_service(self.comm)
        self.stakeholder.communication_service = self.comm

    def _build_clarification_turns_from_messages(self) -> list[ClarificationTurn]:
        """Extract and pair questions/responses from conversation history.

        Returns:
            List of ClarificationTurn objects with matched Q&A pairs
        """
        # Get full conversation between manager and stakeholder
        all_messages = self.comm.get_conversation_history(
            agent_id=self.manager.agent_id,
            other_agent=self.stakeholder.config.agent_id,
            limit=1000,
        )

        logger.info(f"Retrieved {len(all_messages)} messages from conversation history")
        logger.info(
            f"Manager ID: {self.manager.agent_id}, Stakeholder ID: {self.stakeholder.config.agent_id}"
        )

        # Separate questions (from manager) and responses (from stakeholder)
        questions = [
            msg for msg in all_messages if msg.sender_id == self.manager.agent_id
        ]
        responses = [
            msg
            for msg in all_messages
            if msg.sender_id == self.stakeholder.config.agent_id
        ]

        logger.info(f"Found {len(questions)} questions and {len(responses)} responses")

        # Build turns by pairing questions with their responses
        turns: list[ClarificationTurn] = []
        for turn_idx, question_msg in enumerate(questions):
            # Find first response after this question (chronological matching)
            matching_response = None
            response_msg_id = None

            for resp_msg in responses:
                if resp_msg.timestamp > question_msg.timestamp:
                    matching_response = resp_msg.content
                    response_msg_id = str(resp_msg.message_id)
                    # Remove from list so we don't match it again
                    responses = [
                        r for r in responses if r.message_id != resp_msg.message_id
                    ]
                    break

            turns.append(
                ClarificationTurn(
                    turn=turn_idx,
                    timestep=turn_idx,
                    manager_question=question_msg.content,
                    stakeholder_response=matching_response,
                    timestamp=question_msg.timestamp,
                    question_message_id=str(question_msg.message_id),
                    response_message_id=response_msg_id,
                )
            )

        return turns

    def _build_pre_execution_log(
        self,
        clarification_turns: list[ClarificationTurn],
        rubric_specs: list[ManagerAgentGeneratedRubric],
        completion_reason: str,
        total_turns: int,
        started_at: datetime,
    ) -> PreExecutionLog:
        """Construct the final pre-execution log.

        Args:
            clarification_turns: List of clarification turn objects
            rubric_records: List of generated rubric records
            completion_reason: Why the phase ended
            total_turns: Total number of turns executed
            started_at: When the phase started

        Returns:
            Complete PreExecutionLog object
        """
        response = PreExecutionLog(
            clarification_turns=clarification_turns,
            generated_rubrics=rubric_specs,
            completion_reason=completion_reason,
            total_turns=total_turns,
            max_turns_reached=(completion_reason == "max_turns_reached"),
            started_at=started_at,
            completed_at=datetime.now(),
            stakeholder_id=self.stakeholder.config.agent_id,
            manager_id=self.manager.agent_id,
            exemplar_output=self.stakeholder.exemplar_output,  # type: ignore
            max_turns_budget=self.max_turns,
        )
        return response

    async def run(
        self,
        workflow: "Workflow",
    ) -> None:
        """Run pre-execution clarification phase and save log to workflow.metadata.

        Args:
            workflow: Workflow to prepare (metadata will be updated)
            preferences: Preference weights (unused for now)
        """
        # Store manager_id in metadata so actions can use it for sending messages
        if "decomposition_state" not in workflow.metadata:
            workflow.metadata["decomposition_state"] = {}
        workflow.metadata["decomposition_state"]["manager_id"] = self.manager.agent_id
        logger.info(
            f"Pre-execution phase: Manager ID = {self.manager.agent_id}, Stakeholder ID = {self.stakeholder.config.agent_id}"
        )

        started_at = datetime.now()
        completion_reason = "unknown"
        total_turns = 0
        rubric_specs: list[ManagerAgentGeneratedRubric] = []
        rubric_metadata: list[tuple[int, int, str]] = []  # (turn, timestep, pref_name)

        # Main dialogue loop
        for turn in range(self.max_turns):
            logger.info(f"📍 Pre-execution turn {turn + 1}/{self.max_turns}")

            # 1. Stakeholder responds to pending questions
            await self.stakeholder.policy_step(
                current_timestep=turn,
                communication_service=self.comm,
            )

            # 2. Manager observes and acts
            observation = await self.manager.create_observation(
                workflow=workflow,
                execution_state=ExecutionState.INITIALIZED,
                current_timestep=turn,
            )

            action = await self.manager.take_action(observation)

            action_result = await action.execute(
                workflow=workflow,
                communication_service=self.comm,
            )

            # Track rubric generation (completion signal)
            if (
                isinstance(action, GeneratePreferenceRubricAction)
                and action_result.success
            ):
                pref_name = action_result.data.get("preference_name")
                rubric_spec_dict = action_result.data.get("rubric_spec")

                if pref_name and rubric_spec_dict:
                    logger.info(
                        f"✅ Rubric generated for '{pref_name}' - pre-execution phase complete"
                    )
                    rubric_specs.append(
                        ManagerAgentGeneratedRubric.model_validate(rubric_spec_dict)
                    )
                    rubric_metadata.append((turn, turn, pref_name))
                    completion_reason = "all_rubrics_generated"
                    total_turns = turn + 1
                    break
        else:
            # Max turns reached without completion
            logger.warning(
                f"⚠️ Pre-execution phase reached max turns ({self.max_turns}) without generating rubrics"
            )
            completion_reason = "max_turns_reached"
            total_turns = self.max_turns

        # Build log components from communication history
        clarification_turns = self._build_clarification_turns_from_messages()
        logger.info(
            f"Building pre-execution log: {len(clarification_turns)} turns, {len(rubric_specs)} rubrics"
        )
        log = self._build_pre_execution_log(
            clarification_turns=clarification_turns,
            rubric_specs=rubric_specs,
            completion_reason=completion_reason,
            total_turns=total_turns,
            started_at=started_at,
        )

        # Save log to workflow metadata
        if "pre_execution_logs" not in workflow.metadata:
            workflow.metadata["pre_execution_logs"] = []
        workflow.metadata["pre_execution_logs"].append(log.model_dump())

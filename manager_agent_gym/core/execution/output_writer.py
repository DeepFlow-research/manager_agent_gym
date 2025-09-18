"""
Serialization utilities for workflow execution outputs.

This module centralizes all file writing for timestep data, workflow snapshots,
execution logs, and evaluation outputs.
"""

from __future__ import annotations

import json
from typing import Any, Sequence

from ..common.logging import logger
from ...schemas.config import OutputConfig
from ...schemas.core.workflow import Workflow
from ...schemas.unified_results import ExecutionResult
from ..manager_agent import ManagerAgent
from ...schemas.preferences.preference import (
    PreferenceWeights,
)
from ..communication.service import CommunicationService
from ...schemas.execution.manager_actions import ActionResult


class WorkflowSerialiser:
    def __init__(
        self,
        output_config: OutputConfig,
        communication_service: CommunicationService,
        workflow: Workflow,
    ) -> None:
        self.output_config = output_config
        self.communication_service = communication_service
        self.workflow = workflow

    def ensure_directories(self) -> None:
        try:
            self.output_config.ensure_directories_exist()
        except Exception:
            logger.error("failed to create output directories", exc_info=True)

    def save_timestep(
        self,
        timestep_result: ExecutionResult,
        workflow: Workflow,
        current_timestep: int,
        manager_agent: ManagerAgent | None,
        stakeholder_weights: PreferenceWeights | None,
    ) -> None:
        """Write timestep result and a full workflow snapshot for this timestep."""
        # 1) Write timestep result
        try:
            filepath = self.output_config.get_timestep_file_path(current_timestep)
            filepath.parent.mkdir(parents=True, exist_ok=True)
            with open(filepath, "w") as f:
                data = timestep_result.model_dump(mode="json")
                # Add headline cumulative hours for convenience in per-timestep files
                try:
                    data["cumulative_workflow_hours"] = float(
                        workflow.total_simulated_hours
                    )
                except Exception:
                    data["cumulative_workflow_hours"] = "FAILED_TO_CALCULATE"
                json.dump(data, f, indent=2, default=str)
        except Exception:
            logger.error("failed writing timestep result", exc_info=True)

        # 2) Build agent list with dynamic state
        try:
            agents_serialized: list[dict[str, Any]] = []
            for agent in workflow.agents.values():
                try:
                    agent_id = agent.agent_id
                except Exception:
                    agent_id = "unknown"
                try:
                    agent_type = agent.agent_type
                except Exception:
                    agent_type = "unknown"
                try:
                    agent_config_json = agent.config.model_dump(mode="json")  # type: ignore[attr-defined]
                except Exception:
                    agent_config_json = None

                dynamic_fields = {
                    "is_available": agent.is_available,
                    "current_task_ids": [str(t) for t in agent.current_task_ids],
                    "tasks_completed": agent.tasks_completed,
                    "max_concurrent_tasks": agent.max_concurrent_tasks,
                }

                agents_serialized.append(
                    {
                        "agent_id": agent_id,
                        "agent_type": agent_type,
                        "config": agent_config_json,
                        "state": dynamic_fields,
                    }
                )

            # Manager snapshot (safe subset)
            manager_state: dict[str, Any] | None = None
            try:
                if manager_agent is not None:
                    recent_briefs = manager_agent.get_action_buffer(10)
                    try:
                        recent_serialized = [
                            b.model_dump(mode="json") for b in recent_briefs
                        ]
                    except Exception:
                        recent_serialized = []
                    manager_state = {
                        "agent_id": manager_agent.agent_id,
                        "recent_action_briefs": recent_serialized,
                        "current_preference_weights": (
                            stakeholder_weights.get_preference_dict()
                            if stakeholder_weights is not None
                            else None
                        ),
                    }
            except Exception:
                manager_state = None

            # Stakeholder snapshot (safe subset)
            try:
                stakeholder_state = (
                    {
                        "timestep": current_timestep,
                        "weights": stakeholder_weights.get_preference_dict(),
                        "preference_names": stakeholder_weights.get_preference_names(),
                    }
                    if stakeholder_weights is not None
                    else None
                )
            except Exception:
                stakeholder_state = None

            workflow_snapshot = {
                **workflow.model_dump(
                    mode="json", exclude={"agents", "success_criteria"}
                ),
                "agents": agents_serialized,
                "success_criteria": [],
                "timestep": current_timestep,
                "manager_state": manager_state,
                "stakeholder_state": stakeholder_state,
                # Explicit headline figure for convenience
                "cumulative_workflow_hours": (
                    float(workflow.total_simulated_hours)
                    if isinstance(workflow.total_simulated_hours, (int, float))
                    else "FAILED_TO_CALCULATE"
                ),
            }

            wf_dir = self.output_config.workflow_dir
            if wf_dir is not None:
                try:
                    wf_dir.mkdir(parents=True, exist_ok=True)
                except Exception:
                    pass
                snapshot_name = f"workflow_execution_{self.output_config.run_id}_t{current_timestep:04d}.json"
                with open(wf_dir / snapshot_name, "w") as wf_f:
                    json.dump(workflow_snapshot, wf_f, indent=2, default=str)
        except Exception:
            logger.error("failed writing per-timestep workflow snapshot", exc_info=True)

    def save_workflow_summary(
        self,
        workflow: Workflow,
        completed_task_ids: set,
        failed_task_ids: set,
        current_timestep: int,
    ) -> None:
        """Write final workflow snapshot into workflow_outputs directory."""
        try:
            agents_serialized = []
            for agent in workflow.agents.values():
                try:
                    agent_id = agent.agent_id
                except Exception:
                    agent_id = "unknown"
                try:
                    agent_type = agent.agent_type
                except Exception:
                    agent_type = "unknown"
                try:
                    agent_config_json = agent.config.model_dump(mode="json")  # type: ignore[attr-defined]
                except Exception:
                    agent_config_json = None

                agents_serialized.append(
                    {
                        "agent_id": agent_id,
                        "agent_type": agent_type,
                        "config": agent_config_json,
                    }
                )

            snapshot = {
                **workflow.model_dump(mode="json", exclude={"agents"}),
                "agents": agents_serialized,
                "is_complete": workflow.is_complete(),
                "total_tasks": len(workflow.tasks),
                "completed_tasks": len(completed_task_ids),
                "failed_tasks": len(failed_task_ids),
                "timesteps": current_timestep,
                # Headline cumulative hours across all tasks (simulated)
                "cumulative_workflow_hours": (
                    float(workflow.total_simulated_hours)
                    if isinstance(workflow.total_simulated_hours, (int, float))
                    else "FAILED_TO_CALCULATE"
                ),
            }
            path = self.output_config.get_workflow_summary_path()
            with open(path, "w") as f:
                json.dump(snapshot, f, indent=2, default=str)
        except Exception:
            logger.error("save_workflow_summary failed", exc_info=True)

    def save_execution_logs(
        self, manager_action_history: Sequence[tuple[int, ActionResult | None]]
    ) -> None:
        """Write manager actions into execution_logs directory."""
        try:
            run_id = self.output_config.run_id or "run"
            exec_dir = self.output_config.execution_logs_dir
            if exec_dir is None:
                return
            try:
                exec_dir.mkdir(parents=True, exist_ok=True)
            except Exception:
                pass
            path = exec_dir / f"execution_log_{run_id}.json"

            actions: list[dict[str, Any]] = []
            for ts, act in manager_action_history:
                try:
                    if act is None:
                        actions.append(
                            {"timestep": ts, "action_type": None, "action": None}
                        )
                    else:
                        actions.append(
                            {
                                "timestep": ts,
                                "action_type": act.action_type,
                                "action": act.model_dump(mode="json"),
                            }
                        )
                except Exception:
                    actions.append(
                        {"timestep": ts, "action_type": None, "action": None}
                    )

            payload = {"run_id": run_id, "manager_actions": actions}
            with open(path, "w") as f:
                json.dump(payload, f, indent=2, default=str)
        except Exception:
            logger.error("save_execution_logs failed", exc_info=True)

    def save_evaluation_outputs(
        self, evaluation_results: list[Any], reward_vector: list[float] | None = None
    ) -> None:
        """Save evaluation history, reward vector, and final evaluation into evaluation_outputs directory."""
        ev_dir = self.output_config.evaluation_dir
        if ev_dir is None:
            return
        try:
            ev_dir.mkdir(parents=True, exist_ok=True)
        except Exception:
            pass

        # Save full history
        try:
            history_path = self.output_config.get_evaluation_results_path(
                timestamp=self.output_config.run_id
            )
            with open(history_path, "w") as f:
                history_payload = {
                    "evaluation_history": [
                        er.model_dump(mode="json") for er in evaluation_results
                    ],
                    "reward_vector": list(reward_vector or []),
                }
                json.dump(history_payload, f, indent=2, default=str)
        except Exception:
            logger.error("failed saving evaluation history", exc_info=True)

        # Save final only
        try:
            if evaluation_results:
                final_eval = evaluation_results[-1]
                final_path = (
                    ev_dir / f"final_evaluation_{self.output_config.run_id}.json"
                )
                with open(final_path, "w") as f:
                    json.dump(
                        final_eval.model_dump(mode="json"), f, indent=2, default=str
                    )
        except Exception:
            logger.error("failed saving final evaluation", exc_info=True)

    def _serialize_agents_for_snapshot(self) -> list[dict]:
        serialized: list[dict] = []
        for agent in self.workflow.agents.values():
            try:
                agent_id = agent.agent_id
            except Exception:
                agent_id = "unknown"
            try:
                agent_type = agent.agent_type
            except Exception:
                agent_type = "unknown"
            try:
                agent_config_json = agent.config.model_dump(mode="json")
            except Exception:
                agent_config_json = None

            serialized.append(
                {
                    "agent_id": agent_id,
                    "agent_type": agent_type,
                    "config": agent_config_json,
                }
            )
        return serialized

"""
State restoration utilities for rebuilding workflow states from simulation snapshots.

This module handles the complex task of reconstructing complete workflow execution
state from saved simulation data, enabling re-evaluation of past states.
"""

import json
from pathlib import Path
from datetime import datetime
from uuid import UUID
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from manager_agent_gym.core.agents.workflow_agents import AgentRegistry

from manager_agent_gym.core.common.logging import logger
from manager_agent_gym.core.agents.manager_agent.actions import ActionResult
from manager_agent_gym.schemas.domain.communication import Message, MessageType
from manager_agent_gym.schemas.domain.task import TaskStatus


class WorkflowStateRestorer:
    """
    Handles restoration of complete workflow state from simulation snapshots.

    This class encapsulates all the logic needed to rebuild:
    - Workflow task states (status, costs, durations, assignments)
    - Workflow resource states (content, descriptions, artifacts)
    - Stakeholder preferences
    - Communication message history
    - Manager agent action buffer
    - Active agent registry
    - Agent workload assignments
    """

    def __init__(self, snapshot_dir: str, timestep: int):
        """
        Initialize the state restorer for a specific snapshot.

        Args:
            snapshot_dir: Path to simulation run directory
            timestep: Target timestep to restore from
        """
        self.snapshot_dir = Path(snapshot_dir)
        self.timestep = timestep
        self.timestep_data: dict[str, Any] = {}
        self.execution_log_data: dict[str, Any] = {}

    def load_snapshot_data(self) -> None:
        """Load all necessary snapshot data files."""
        # Load timestep snapshot
        timestep_file = (
            self.snapshot_dir / "timestep_data" / f"timestep_{self.timestep:04d}.json"
        )
        if not timestep_file.exists():
            raise FileNotFoundError(f"Timestep file not found: {timestep_file}")

        with open(timestep_file, "r") as f:
            self.timestep_data = json.load(f)

        # Load execution log for manager action buffer
        execution_log_file = (
            self.snapshot_dir
            / "execution_logs"
            / f"execution_log_{self.snapshot_dir.name.split('_')[-1]}.json"
        )
        if execution_log_file.exists():
            with open(execution_log_file, "r") as f:
                self.execution_log_data = json.load(f)
        else:
            logger.warning("Execution log not found: %s", execution_log_file)

    def restore_workflow_state(self, workflow) -> None:
        """Update workflow task and resource states from snapshot."""
        workflow_snapshot = self.timestep_data["metadata"]["workflow_snapshot"]

        # Update task states
        tasks_data = workflow_snapshot.get("tasks", {})
        for task_id_str, task_data in tasks_data.items():
            task_id = UUID(task_id_str)
            if task_id in workflow.tasks:
                task = workflow.tasks[task_id]
                # Update key state information
                task.status = TaskStatus(task_data["status"])
                task.assigned_agent_id = task_data.get("assigned_agent_id")
                task.actual_duration_hours = task_data.get("actual_duration_hours")
                task.actual_cost = task_data.get("actual_cost")
                task.quality_score = task_data.get("quality_score")
                if task_data.get("started_at"):
                    task.started_at = datetime.fromisoformat(task_data["started_at"])
                if task_data.get("completed_at"):
                    task.completed_at = datetime.fromisoformat(
                        task_data["completed_at"]
                    )
                task.execution_notes = task_data.get("execution_notes", [])

        # Synchronize embedded subtasks with the updated registry to fix status inconsistencies
        for task in workflow.tasks.values():
            task.sync_embedded_tasks_with_registry(workflow.tasks)

        # Restore resources from snapshot
        resources_data = workflow_snapshot.get("resources", {})
        logger.info("Restoring %s resources from snapshot", len(resources_data))

        # Import Resource here to avoid circular imports
        from manager_agent_gym.schemas.domain.resource import Resource
        import tempfile
        from pathlib import Path

        for resource_id_str, resource_data in resources_data.items():
            resource_id = UUID(resource_id_str)

            # Handle backward compatibility: convert old inline content to files
            if "file_path" in resource_data:
                # New format: file-based resource
                resource = Resource(
                    id=resource_id,
                    name=resource_data["name"],
                    description=resource_data["description"],
                    file_path=resource_data["file_path"],
                    mime_type=resource_data.get("mime_type", "text/plain"),
                    size_bytes=resource_data.get("size_bytes", 0),
                    file_format_metadata=resource_data.get("file_format_metadata"),
                )
            else:
                # Old format: inline content - migrate to file
                content = resource_data.get("content", "")
                content_type = resource_data.get("content_type", "text/plain")

                # Save to temp file
                temp_dir = Path(tempfile.mkdtemp(prefix="restored_resource_"))
                ext = ".md" if "text" in content_type else ".bin"
                temp_file = temp_dir / f"resource_{resource_id}{ext}"

                if isinstance(content, str):
                    temp_file.write_text(content, encoding="utf-8")
                else:
                    temp_file.write_bytes(
                        content if isinstance(content, bytes) else str(content).encode()
                    )

                resource = Resource(
                    id=resource_id,
                    name=resource_data["name"],
                    description=resource_data["description"],
                    file_path=str(temp_file.absolute()),
                    mime_type=content_type,
                    size_bytes=temp_file.stat().st_size,
                )

            workflow.resources[resource_id] = resource

        # Update workflow-level state
        workflow.total_cost = workflow_snapshot.get("total_cost", 0.0)
        if workflow_snapshot.get("started_at"):
            workflow.started_at = datetime.fromisoformat(
                workflow_snapshot["started_at"]
            )
        if workflow_snapshot.get("completed_at"):
            workflow.completed_at = datetime.fromisoformat(
                workflow_snapshot["completed_at"]
            )
        workflow.is_active = workflow_snapshot.get("is_active", True)

    def restore_stakeholder_preferences(self, stakeholder_agent) -> None:
        """Update stakeholder agent state to match snapshot."""
        prefs_data = self.timestep_data["metadata"]["stakeholder_preference_state"]

        # Use stakeholder's restore_from_state hook
        stakeholder_agent.restore_from_state(prefs_data)

    def restore_communication_history(self, communication_service) -> None:
        """Restore communication message history from snapshot."""
        # Messages are stored in manager_observation.recent_messages
        manager_observation = self.timestep_data["metadata"]["manager_observation"]
        messages = manager_observation.get("recent_messages", [])

        logger.info("Restoring %s messages from snapshot", len(messages))

        for i, msg_data in enumerate(messages):
            try:
                # Convert snapshot data to Message object
                message = Message(
                    message_id=UUID(msg_data["message_id"]),
                    sender_id=msg_data["sender_id"],
                    receiver_id=msg_data.get("receiver_id"),
                    recipients=msg_data.get("recipients", []),
                    content=msg_data["content"],
                    message_type=MessageType(msg_data["message_type"]),
                    timestamp=datetime.fromisoformat(msg_data["timestamp"]),
                    thread_id=UUID(msg_data["thread_id"])
                    if msg_data.get("thread_id")
                    else None,
                    parent_message_id=UUID(msg_data["parent_message_id"])
                    if msg_data.get("parent_message_id")
                    else None,
                    related_task_id=UUID(msg_data["related_task_id"])
                    if msg_data.get("related_task_id")
                    else None,
                    priority=msg_data.get("priority", 1),
                    read_by={
                        agent_id: datetime.fromisoformat(read_time)
                        for agent_id, read_time in msg_data.get("read_by", {}).items()
                    },
                    metadata=msg_data.get("metadata", {}),
                )

                # Add message to communication service
                communication_service.graph.add_message(message)

                logger.debug(
                    "Restored message %s: %s -> %s...",
                    i + 1,
                    msg_data["sender_id"],
                    msg_data["content"][:50],
                )

            except Exception as e:
                logger.error(
                    "Failed to restore message %s: %s", i + 1, e, exc_info=True
                )
                continue

        logger.info(
            "Successfully restored %s messages",
            len(communication_service.graph.messages),
        )

    def restore_manager_action_buffer(self, manager_agent) -> None:
        """Restore manager agent action buffer from execution logs."""
        if not self.execution_log_data:
            logger.warning(
                "No execution log data available for manager action buffer restoration"
            )
            return

        manager_actions = self.execution_log_data.get("manager_actions", [])
        logger.info("Found %s manager actions in execution log", len(manager_actions))

        # Filter actions up to our target timestep
        actions_to_restore = [
            action
            for action in manager_actions
            if action.get("timestep", 0) <= self.timestep
        ]

        logger.info(
            "Restoring %s manager actions up to timestep %s",
            len(actions_to_restore),
            self.timestep,
        )

        restored_count = 0
        for entry in actions_to_restore:
            try:
                payload = entry.get("action")
                if not payload:
                    continue
                # Reconstruct ActionResult directly from serialized payload
                restored = ActionResult.model_validate(payload)
                if restored.timestep is None:
                    restored.timestep = entry.get("timestep")
                manager_agent.record_action(restored)
                restored_count += 1
            except Exception as e:
                logger.debug(
                    "Skipping invalid manager action entry during restoration: %s",
                    e,
                    exc_info=True,
                )
                continue

        logger.info("Restored %s manager actions into manager buffer", restored_count)

    def restore_active_agents(self, agent_registry: "AgentRegistry") -> None:
        """Restore active agent states from snapshot."""
        workflow_snapshot = self.timestep_data["metadata"]["workflow_snapshot"]
        agents_data = workflow_snapshot.get("agents", [])

        logger.info("Restoring %s active agents from snapshot", len(agents_data))

        for agent_data in agents_data:
            agent_id = agent_data.get("agent_id")
            agent_type = agent_data.get("agent_type", "ai")

            if (
                agent_id and agent_id != "stakeholder_balanced"
            ):  # Skip stakeholder agent
                logger.debug(
                    "Active agent from snapshot: %s (%s)", agent_id, agent_type
                )
                # TODO: Properly restore agent states to registry
                # This depends on AgentRegistry interface

    def get_agent_workloads(self) -> dict[str, list[str]]:
        """Extract current task assignments per agent from workflow state."""
        workflow_snapshot = self.timestep_data["metadata"]["workflow_snapshot"]
        tasks_data = workflow_snapshot.get("tasks", {})

        workloads: dict[str, list[str]] = {}

        for task_id, task_data in tasks_data.items():
            assigned_agent = task_data.get("assigned_agent_id")
            if assigned_agent:
                if assigned_agent not in workloads:
                    workloads[assigned_agent] = []
                workloads[assigned_agent].append(
                    f"{task_data.get('name', task_id)} ({task_data.get('status')})"
                )

        return workloads

    def get_simulated_time_state(self) -> dict[str, Any]:
        """Extract simulated time information from snapshot."""
        return {
            "simulated_duration_hours": self.timestep_data.get(
                "simulated_duration_hours", 0.0
            ),
            "execution_time_seconds": self.timestep_data.get(
                "execution_time_seconds", 0.0
            ),
            "timestep": self.timestep,
            "completed_at": self.timestep_data.get("completed_at"),
        }

"""
State restoration utilities for rebuilding workflow states from simulation snapshots.

This module handles the complex task of reconstructing complete workflow execution
state from saved simulation data, enabling re-evaluation of past states.
"""

import json
from pathlib import Path
from datetime import datetime
from uuid import UUID
from typing import Any

from ..workflow_agents.registry import AgentRegistry
from ...schemas.core.communication import Message, MessageType
from ...schemas.core.tasks import TaskStatus
from ...schemas.preferences.preference import PreferenceWeights, Preference


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
            print(f"⚠️  Execution log not found: {execution_log_file}")

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
        print(f"📋 Restoring {len(resources_data)} resources from snapshot")

        # Import Resource here to avoid circular imports
        from ...schemas.core.resources import Resource

        for resource_id_str, resource_data in resources_data.items():
            resource_id = UUID(resource_id_str)
            resource = Resource(
                id=resource_id,
                name=resource_data["name"],
                description=resource_data["description"],
                content=resource_data.get("content"),
                content_type=resource_data.get("content_type", "text/plain"),
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
        """Update stakeholder agent preferences to match snapshot."""
        prefs_data = self.timestep_data["metadata"]["stakeholder_preference_state"]

        stakeholder_agent.apply_preference_change(
            timestep=self.timestep,
            new_weights=PreferenceWeights(
                preferences=[
                    Preference(name=key, weight=value)
                    for key, value in prefs_data["weights"].items()
                ]
            ),
            change_event=None,
        )

    def restore_communication_history(self, communication_service) -> None:
        """Restore communication message history from snapshot."""
        # Messages are stored in manager_observation.recent_messages
        manager_observation = self.timestep_data["metadata"]["manager_observation"]
        messages = manager_observation.get("recent_messages", [])

        print(f"📬 Restoring {len(messages)} messages from snapshot")

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

                print(
                    f"  ✅ Message {i + 1}: {msg_data['sender_id']} -> {msg_data['content'][:50]}..."
                )

            except Exception as e:
                print(f"  ❌ Failed to restore message {i + 1}: {e}")
                continue

        print(
            f"📬 Successfully restored {len(communication_service.graph.messages)} messages"
        )

    def restore_manager_action_buffer(self, manager_agent) -> None:
        """Restore manager agent action buffer from execution logs."""
        if not self.execution_log_data:
            print(
                "⚠️  No execution log data available for manager action buffer restoration"
            )
            return

        # TODO: Implement manager action buffer restoration
        # Need to examine execution log structure first
        manager_actions = self.execution_log_data.get("manager_actions", [])
        print(f"🎯 Found {len(manager_actions)} manager actions in execution log")

        # Filter actions up to our target timestep
        actions_to_restore = [
            action
            for action in manager_actions
            if action.get("timestep", 0) <= self.timestep
        ]

        print(
            f"🎯 Restoring {len(actions_to_restore)} manager actions up to timestep {self.timestep}"
        )

        # TODO: Add actions to manager agent buffer
        # This depends on the manager agent's action buffer interface

    def restore_active_agents(self, agent_registry: AgentRegistry) -> None:
        """Restore active agent states from snapshot."""
        workflow_snapshot = self.timestep_data["metadata"]["workflow_snapshot"]
        agents_data = workflow_snapshot.get("agents", [])

        print(f"👥 Restoring {len(agents_data)} active agents from snapshot")

        for agent_data in agents_data:
            agent_id = agent_data.get("agent_id")
            agent_type = agent_data.get("agent_type", "ai")

            if (
                agent_id and agent_id != "stakeholder_balanced"
            ):  # Skip stakeholder agent
                print(f"  ✅ Agent: {agent_id} ({agent_type})")
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

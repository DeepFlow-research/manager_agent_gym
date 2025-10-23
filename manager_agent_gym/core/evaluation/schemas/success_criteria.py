"""
Success criteria schemas for workflow, task, and resource validation.

Provides unified validation context with multimodal file access for evaluation rules.
"""

from pathlib import Path
from typing import Callable, Any, Awaitable
from uuid import UUID
from pydantic import BaseModel, Field, PrivateAttr
from enum import Enum

from manager_agent_gym.schemas.domain.workflow import Workflow
from manager_agent_gym.schemas.domain.resource import Resource
from manager_agent_gym.schemas.domain.communication import (
    SenderMessagesView,
    ThreadMessagesView,
)
from manager_agent_gym.core.agents.manager_agent.actions import ActionResult
from manager_agent_gym.schemas.preferences import PreferenceSnapshot
from manager_agent_gym.core.agents.workflow_agents.schemas.telemetry import (
    AgentPublicState,
    AgentToolUseEvent,
)


class ValidationLevel(str, Enum):
    """Level at which validation is applied."""

    WORKFLOW = "workflow"
    TASK = "task"
    RESOURCE = "resource"
    PREFERENCE = "preference"


class ValidationFrequency(str, Enum):
    """Frequency at which validation rules are executed."""

    MANUAL = "manual"  # Only when explicitly called
    ON_COMPLETION = "on_completion"  # When task/workflow completes
    EVERY_TIMESTEP = "every_timestep"  # Every execution timestep


class ValidationMeta(BaseModel):
    """Metadata for validation results."""

    execution_time: float = Field(
        default=0.0, description="Time taken to execute validation in seconds"
    )
    error: str | None = Field(
        default=None, description="Error message if validation failed to run"
    )
    details: dict[str, Any] = Field(
        default_factory=dict, description="Additional validation details"
    )


class ValidationResult(BaseModel):
    """Result of running a single validation rule."""

    name: str = Field(..., description="Name of the validation rule")
    score: float = Field(default=1.0, description="Numeric score achieved")
    max_score: float = Field(default=1.0, description="Maximum possible score")
    passed: bool = Field(..., description="Whether the validation passed")
    message: str = Field(..., description="Human-readable result message")
    level: ValidationLevel = Field(..., description="Level of validation")
    # Optional metric grouping for higher-level aggregation (e.g., "quality", "safety")
    metric: str | None = Field(
        default=None, description="Logical metric this result contributes to"
    )
    # Optional rule weight for aggregation within a metric
    weight: float = Field(
        default=1.0, ge=0.0, description="Weight for metric aggregation"
    )
    meta: ValidationMeta = Field(
        default_factory=ValidationMeta, description="Validation metadata"
    )

    @property
    def normalized_score(self) -> float:
        """Return score normalized to [0,1] range."""
        return self.score / self.max_score if self.max_score > 0 else 0.0

    @property
    def regret(self) -> float:
        """Direct regret calculation: gap from perfect score."""
        return max(0.0, self.max_score - self.score) / self.max_score


class FileAccessor:
    """Helper for accessing resource files in validation rules.

    Provides clean API for code rules to read files without dealing with
    Resource objects directly.
    """

    def __init__(self, resources: dict[UUID, Resource]):
        """
        Initialize file accessor with resources.

        Args:
            resources: Dictionary mapping resource IDs to Resource objects
        """
        self._resources = resources

    def get_path(self, resource_id: str | UUID) -> Path:
        """
        Get file path for a resource.

        Args:
            resource_id: Resource UUID (as string or UUID)

        Returns:
            Path object for the resource file

        Raises:
            ValueError: If resource not found
        """
        rid = UUID(resource_id) if isinstance(resource_id, str) else resource_id
        resource = self._resources.get(rid)
        if not resource:
            raise ValueError(f"Resource {resource_id} not found")
        return Path(resource.file_path)

    def read_bytes(self, resource_id: str | UUID) -> bytes:
        """
        Read resource as bytes.

        Args:
            resource_id: Resource UUID

        Returns:
            File content as bytes
        """
        return self.get_path(resource_id).read_bytes()

    def read_text(self, resource_id: str | UUID) -> str:
        """
        Read resource as text (for markdown, JSON, etc.).

        Args:
            resource_id: Resource UUID

        Returns:
            File content as string
        """
        return self.get_path(resource_id).read_text(encoding="utf-8")

    def read_excel(self, resource_id: str | UUID, sheet_name: str | None = None) -> Any:
        """
        Read Excel resource as DataFrame.

        Args:
            resource_id: Resource UUID
            sheet_name: Optional sheet name (reads first sheet if None)

        Returns:
            pandas DataFrame
        """
        import pandas as pd  # type: ignore

        path = self.get_path(resource_id)
        return pd.read_excel(path, sheet_name=sheet_name)

    def read_csv(self, resource_id: str | UUID) -> Any:
        """
        Read CSV resource as DataFrame.

        Args:
            resource_id: Resource UUID

        Returns:
            pandas DataFrame
        """
        import pandas as pd  # type: ignore

        path = self.get_path(resource_id)
        return pd.read_csv(path)

    def read_pdf_text(self, resource_id: str | UUID) -> str:
        """
        Extract text from PDF resource.

        Args:
            resource_id: Resource UUID

        Returns:
            Extracted text from all pages
        """
        import pdfplumber

        path = self.get_path(resource_id)
        with pdfplumber.open(path) as pdf:
            pages = []
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    pages.append(text)
            return "\n\n".join(pages)

    def read_docx_text(self, resource_id: str | UUID) -> str:
        """
        Extract text from DOCX resource.

        Args:
            resource_id: Resource UUID

        Returns:
            Extracted text from all paragraphs
        """
        from docx import Document  # type: ignore

        path = self.get_path(resource_id)
        doc = Document(str(path))
        return "\n".join(p.text for p in doc.paragraphs)

    def get_resource(self, resource_id: str | UUID) -> Resource:
        """
        Get full Resource object.

        Args:
            resource_id: Resource UUID

        Returns:
            Resource object

        Raises:
            ValueError: If resource not found
        """
        rid = UUID(resource_id) if isinstance(resource_id, str) else resource_id
        resource = self._resources.get(rid)
        if not resource:
            raise ValueError(f"Resource {resource_id} not found")
        return resource


class ValidationContext(BaseModel):
    """Context information provided to validation rules.
    
    Provides:
    - Direct file access via .files property (multimodal support)
    - Helper methods to get task outputs
    - Legacy optional context fields for backward compatibility
    
    Example usage in code rules:
        ```python
        def evaluate(workflow: Workflow, context: ValidationContext) -> float:
            # Use context helpers to access resources
            
            # Get primary output (first output of last task)
            output = context.get_primary_output()
            if not output or not output.is_spreadsheet:
                return 0.0
            
            # Use file accessor for multimodal resources:
            df = context.files.read_excel(output.id, sheet_name='Analysis')
            text = context.files.read_pdf_text(output.id)
            
            # Or get all outputs
            all_outputs = context.get_all_outputs()
            
            return score
        ```
    """

    model_config = {"arbitrary_types_allowed": True}

    workflow: Workflow
    current_preferences: PreferenceSnapshot | None = None
    timestep: int = 0
    # Selectively included, typed supplemental context (only set when requested)
    manager_actions: list[ActionResult] | None = None
    communications_by_sender: list[SenderMessagesView] | None = None
    communications_by_thread: list[ThreadMessagesView] | None = None
    preference_history: list[dict[str, Any]] | None = None
    stakeholder_profile: dict[str, Any] | None = None
    resources_by_task: dict[UUID, list] | None = None
    all_resources: list | None = None
    agent_public_states: dict[str, AgentPublicState] | None = None
    agent_tool_usage_by_task: dict[UUID, list[AgentToolUseEvent]] | None = None

    # Private attributes for enhanced functionality (not serialized)
    _file_accessor: FileAccessor | None = PrivateAttr(default=None)
    _explicit_resources: list | None = PrivateAttr(default=None)

    @property
    def files(self) -> FileAccessor:
        """
        Access resource files with helper methods.
        
        Provides convenient methods for reading multimodal resources:
        - context.files.read_excel(resource_id, sheet_name="Sheet1")
        - context.files.read_pdf_text(resource_id)
        - context.files.read_csv(resource_id)
        - context.files.read_docx_text(resource_id)
        - context.files.get_path(resource_id)

        Returns:
            FileAccessor with read methods for various file types
        """
        if self._file_accessor is None:
            self._file_accessor = FileAccessor(self.workflow.resources)
        return self._file_accessor

    def set_evaluable_resources(self, resources: list[Any]) -> None:
        """
        Override resources for this evaluation context.

        Used in multi-agent ranking to provide the specific variant's resource bundle
        instead of looking up resources from task.output_resource_ids.

        Args:
            resources: List of resources to evaluate
        """
        self._explicit_resources = resources

    def get_task_outputs(self, task_name: str | None = None) -> list[Resource]:
        """
        Get output resources from a task.

        Args:
            task_name: Task name (or last task if None)

        Returns:
            List of Resource objects for task outputs
        """
        from manager_agent_gym.schemas.domain.workflow import Task

        task: Task | None = None

        if task_name:
            # Find task by name
            task = next(
                (t for t in self.workflow.tasks.values() if t.name == task_name), None
            )
        else:
            # Get last task (most recent in execution order)
            if self.workflow.tasks:
                # Get task with highest timestep or last in dict
                sorted_tasks = sorted(
                    self.workflow.tasks.values(),
                    key=lambda t: getattr(t, "timestep", 0),
                )
                task = sorted_tasks[-1] if sorted_tasks else None

        if not task:
            return []

        return [
            self.workflow.resources[rid]
            for rid in task.output_resource_ids
            if rid in self.workflow.resources
        ]

    def get_primary_output(self) -> Resource | None:
        """
        Get the primary output resource (first output of last task).

        Returns:
            Primary Resource or None if no outputs
        """
        outputs = self.get_task_outputs()
        return outputs[0] if outputs else None

    def get_all_outputs(self) -> list[Resource]:
        """
        Get all output resources from all tasks.

        Returns:
            List of all output Resource objects
        """
        all_outputs = []
        for task in self.workflow.tasks.values():
            outputs = [
                self.workflow.resources[rid]
                for rid in task.output_resource_ids
                if rid in self.workflow.resources
            ]
            all_outputs.extend(outputs)
        return all_outputs

    def get_evaluable_resources(
        self, task_name: str | None = None, include_intermediary: bool = False
    ) -> list[Any]:
        """
        Get resources suitable for evaluation (outputs only by default).
        
        This is the primary method for code rules and LLM evaluators to get
        the resources they should evaluate.

        If explicit resources have been set via set_evaluable_resources(),
        returns those instead of looking them up from the workflow.

        Args:
            task_name: Optional task name to filter to specific task outputs
            include_intermediary: If True, include intermediary resources (default: False)

        Returns:
            List of Resource objects to evaluate
        """
        # If explicit resources set (for multi-agent ranking), return those
        if self._explicit_resources is not None:
            return self._explicit_resources

        # Use helper methods for cleaner logic
        if task_name:
            # Get specific task outputs
            resources = self.get_task_outputs(task_name)
        else:
            # Get all workflow output resources
            resources = self.get_all_outputs()

        # Filter by resource_role if needed
        if not include_intermediary:
            resources = [r for r in resources if r.resource_role == "output"]

        return resources


WorkflowValidatorFunc = Callable[[Workflow], bool | float | Awaitable[bool | float]]

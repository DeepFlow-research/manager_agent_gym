"""
File storage manager for workflow resources.

Provides task-scoped file storage for binary resources (PDFs, images, Excel files, etc.)
with automatic cleanup capabilities.
"""

import shutil
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING
from uuid import UUID

from manager_agent_gym.core.common.logging import logger

if TYPE_CHECKING:
    from manager_agent_gym.schemas.domain.resource import Resource


class ResourceFileManager:
    """
    Manages file storage for workflow resources.

    Provides task-scoped temporary directories for storing binary files
    during task execution. Supports automatic cleanup after task completion.

    Example:
        ```python
        manager = ResourceFileManager(base_dir="/tmp/workflow_files")

        # Get workspace for a task
        workspace = manager.get_workspace_for_task(task_id)

        # Save a resource file
        file_path = manager.save_resource_file(
            resource,
            pdf_content,
            filename="report.pdf"
        )

        # Load it back
        content = manager.load_resource_file(resource)

        # Cleanup after task
        manager.cleanup_task_files(task_id)
        ```
    """

    def __init__(self, base_dir: str | Path | None = None):
        """
        Initialize the resource file manager.

        Args:
            base_dir: Base directory for storing files. If None, uses system temp directory.
        """
        if base_dir is None:
            self.base_dir = Path(tempfile.gettempdir()) / "manager_agent_gym_resources"
        else:
            self.base_dir = Path(base_dir)

        self.base_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"ResourceFileManager initialized with base_dir: {self.base_dir}")

    def get_workspace_for_task(self, task_id: UUID) -> Path:
        """
        Get the workspace directory for a specific task.

        Creates the directory if it doesn't exist.

        Args:
            task_id: Task UUID

        Returns:
            Path to the task's workspace directory
        """
        workspace = self.base_dir / str(task_id)
        workspace.mkdir(parents=True, exist_ok=True)
        return workspace

    def save_resource_file(
        self,
        resource: "Resource",
        content: bytes,
        task_id: UUID | None = None,
        filename: str | None = None,
    ) -> str:
        """
        Save binary content for a resource and update the resource's file_path.

        Args:
            resource: Resource object to save content for
            content: Binary content to save
            task_id: Task ID for workspace scoping. If None, uses resource ID.
            filename: Optional filename. If None, uses resource name with sanitization.

        Returns:
            Absolute path to the saved file
        """
        # Determine workspace
        if task_id:
            workspace = self.get_workspace_for_task(task_id)
        else:
            workspace = self.base_dir / "shared"
            workspace.mkdir(parents=True, exist_ok=True)

        # Determine filename
        if filename is None:
            # Sanitize resource name for filesystem
            filename = self._sanitize_filename(resource.name)

        file_path = workspace / filename

        # Ensure unique filename if it already exists
        if file_path.exists():
            stem = file_path.stem
            suffix = file_path.suffix
            counter = 1
            while file_path.exists():
                file_path = workspace / f"{stem}_{counter}{suffix}"
                counter += 1

        # Save file
        file_path.write_bytes(content)
        logger.debug(
            f"Saved resource {resource.name} to {file_path} ({len(content)} bytes)"
        )

        # Update resource metadata
        resource.file_path = str(file_path.absolute())
        resource.size_bytes = len(content)

        return str(file_path.absolute())

    def load_resource_file(self, resource: "Resource") -> bytes:
        """
        Load binary content from a resource's file path.

        Args:
            resource: Resource object with file_path set

        Returns:
            Binary content of the file

        Raises:
            ValueError: If resource has no file_path
            FileNotFoundError: If file doesn't exist
        """
        if not resource.file_path:
            raise ValueError(f"Resource {resource.name} has no file_path set")

        file_path = Path(resource.file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"Resource file not found: {resource.file_path}")

        return file_path.read_bytes()

    def cleanup_task_files(self, task_id: UUID, force: bool = False) -> bool:
        """
        Remove all files for a specific task.

        Args:
            task_id: Task UUID
            force: If True, ignore errors during cleanup

        Returns:
            True if cleanup was successful, False otherwise
        """
        workspace = self.base_dir / str(task_id)

        if not workspace.exists():
            logger.debug(f"No workspace found for task {task_id}, nothing to clean")
            return True

        try:
            shutil.rmtree(workspace)
            logger.info(f"Cleaned up workspace for task {task_id}")
            return True
        except Exception as e:
            if force:
                logger.warning(f"Failed to cleanup task {task_id} workspace: {e}")
                return False
            else:
                raise

    def cleanup_all(self, force: bool = False) -> None:
        """
        Remove all stored files (use with caution).

        Args:
            force: If True, ignore errors during cleanup
        """
        if self.base_dir.exists():
            try:
                shutil.rmtree(self.base_dir)
                self.base_dir.mkdir(parents=True, exist_ok=True)
                logger.info("Cleaned up all resource files")
            except Exception as e:
                if force:
                    logger.warning(f"Failed to cleanup all files: {e}")
                else:
                    raise

    def get_file_path_for_resource(
        self,
        resource_name: str,
        task_id: UUID | None = None,
        extension: str | None = None,
    ) -> Path:
        """
        Generate a file path for a new resource without saving content.

        Useful for tools that need to know the output path before creating the file.

        Args:
            resource_name: Name of the resource
            task_id: Task ID for workspace scoping
            extension: File extension (with or without dot)

        Returns:
            Path object for the file
        """
        if task_id:
            workspace = self.get_workspace_for_task(task_id)
        else:
            workspace = self.base_dir / "shared"
            workspace.mkdir(parents=True, exist_ok=True)

        filename = self._sanitize_filename(resource_name)

        if extension:
            if not extension.startswith("."):
                extension = f".{extension}"
            if not filename.endswith(extension):
                filename = f"{filename}{extension}"

        file_path = workspace / filename

        # Ensure unique filename
        if file_path.exists():
            stem = file_path.stem
            suffix = file_path.suffix
            counter = 1
            while file_path.exists():
                file_path = workspace / f"{stem}_{counter}{suffix}"
                counter += 1

        return file_path

    @staticmethod
    def _sanitize_filename(name: str) -> str:
        """
        Sanitize a string for use as a filename.

        Removes or replaces characters that aren't safe for filesystems.

        Args:
            name: Original name

        Returns:
            Sanitized filename
        """
        # Replace unsafe characters
        unsafe_chars = '<>:"/\\|?*'
        sanitized = name
        for char in unsafe_chars:
            sanitized = sanitized.replace(char, "_")

        # Remove leading/trailing whitespace and dots
        sanitized = sanitized.strip(". ")

        # Limit length
        if len(sanitized) > 200:
            sanitized = sanitized[:200]

        # Ensure not empty
        if not sanitized:
            sanitized = "unnamed_resource"

        return sanitized

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with optional cleanup."""
        # Note: We don't auto-cleanup on exit by default
        # Cleanup should be explicit via cleanup_task_files or cleanup_all
        return False

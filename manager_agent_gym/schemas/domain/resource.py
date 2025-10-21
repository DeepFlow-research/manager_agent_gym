"""
Resource data models for Manager Agent Gym.
"""

from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class Resource(BaseModel):
    """Workflow resource model.

    Represents inputs/outputs of tasks: documents, datasets, artifacts,
    code snippets, and other digital assets (R in the POSG state).

    Example:
        ```python
        Resource(
            name="Stakeholder Brief v1",
            description="Two-page summary for exec review",
            content="...",
            content_type="text/markdown",
        )
        ```
    """

    id: UUID = Field(
        default_factory=uuid4, description="Unique identifier for the resource"
    )
    name: str = Field(
        ...,
        description="Human-readable resource name",
        examples=["Stakeholder Brief v1"],
    )
    description: str = Field(
        ..., description="What this resource contains and how it is used"
    )

    content: str | None = Field(
        default=None,
        description="Inline content for small artifacts. Large files should be stored externally and referenced here.",
    )
    content_type: str = Field(
        default="text/plain",
        description="MIME type, e.g., text/plain, text/markdown, application/json",
        examples=["text/markdown", "application/json"],
    )

    @property
    def resource_id(self) -> UUID:
        """Alias for id field to maintain compatibility."""
        return self.id

    def pretty_print(self, max_preview_chars: int = 5000) -> str:
        """Return a human-readable summary of the resource with a safe content preview."""
        lines: list[str] = []
        lines.append(f"Resource: {self.name} (ID: {self.id}, type={self.content_type})")
        if self.description:
            lines.append(f"  Description: {self.description}")
        if self.content:
            try:
                word_count = len(self.content.split())
            except Exception:
                word_count = 0
            char_len = len(self.content)
            lines.append(f"  Content stats: words={word_count}, chars={char_len}")
            preview = self.content[:max_preview_chars]
            if len(self.content) > max_preview_chars:
                preview += "... (truncated)"
            lines.append("  Content preview:")
            for line in preview.splitlines()[:60]:
                lines.append(f"    {line}")
        else:
            lines.append("  Content: <empty>")
        return "\n".join(lines)

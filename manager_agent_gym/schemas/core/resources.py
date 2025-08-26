"""
Resource data models for Manager Agent Gym.
"""

from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class Resource(BaseModel):
    """
    A resource in the workflow system.

    Resources represent inputs/outputs of tasks including documents,
    data, code, and other digital assets (R in the POSG state).
    """

    id: UUID = Field(default_factory=uuid4)
    name: str = Field(..., description="Human-readable name")
    description: str = Field(..., description="Detailed description")

    content: str | None = Field(
        default=None, description="Actual content of the resource"
    )
    content_type: str = Field(
        default="text/plain", description="MIME type of the content"
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

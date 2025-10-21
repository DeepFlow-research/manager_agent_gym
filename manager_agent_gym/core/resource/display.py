"""
Resource display utilities - formatting and pretty printing.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from manager_agent_gym.schemas.domain.resource import Resource


class ResourceDisplay:
    """Stateless display service for resource formatting."""

    @staticmethod
    def pretty_print(resource: "Resource", max_preview_chars: int = 5000) -> str:
        """Return a human-readable summary of the resource."""
        lines = [
            f"Resource: {resource.name} (ID: {resource.id}, type={resource.content_type})",
        ]

        if resource.description:
            lines.append(f"  Description: {resource.description}")

        # Preview content if present
        if resource.content:
            try:
                word_count = len(resource.content.split())
            except Exception:
                word_count = 0
            char_len = len(resource.content)
            lines.append(f"  Content stats: words={word_count}, chars={char_len}")
            preview = resource.content[:max_preview_chars]
            if len(resource.content) > max_preview_chars:
                preview += "... (truncated)"
            lines.append("  Content preview:")
            for line in preview.splitlines()[:60]:
                lines.append(f"    {line}")
        else:
            lines.append("  Content: <empty>")

        return "\n".join(lines)

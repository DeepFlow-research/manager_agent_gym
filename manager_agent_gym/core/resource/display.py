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
            f"Resource: {resource.name} (ID: {resource.id}, type={resource.mime_type})",
        ]

        if resource.description:
            lines.append(f"  Description: {resource.description}")

        # File information
        lines.append(f"  File: {resource.file_path}")
        lines.append(f"  Size: {resource.size_bytes:,} bytes")

        if resource.file_format_metadata:
            lines.append(f"  Metadata: {resource.file_format_metadata}")

        # Preview content if text-based
        try:
            if resource.is_text_format:
                content = resource.load_text()
                word_count = len(content.split())
                char_len = len(content)
                lines.append(f"  Content stats: words={word_count}, chars={char_len}")
                preview = content[:max_preview_chars]
                if len(content) > max_preview_chars:
                    preview += "... (truncated)"
                lines.append("  Content preview:")
                for line in preview.splitlines()[:60]:
                    lines.append(f"    {line}")
            else:
                lines.append(f"  Content: <binary file, {resource.size_bytes} bytes>")
        except Exception as e:
            lines.append(f"  Content: <unable to load: {e}>")

        return "\n".join(lines)

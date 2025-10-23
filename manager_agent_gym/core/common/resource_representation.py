"""
Resource representation modes for multimodal LLM inputs.

Defines how different resource types should be presented to LLMs
for optimal token efficiency and task suitability.
"""

from enum import Enum


class ResourceRepresentationMode(str, Enum):
    """How to represent a resource to the LLM.

    Different representation modes optimize for different use cases:
    - VISUAL: For visual inspection, formatting checks, design review
    - DATA: For data analysis, manipulation, computation
    - NATIVE: For native file handling (PDF/audio/video via API)
    - AUTO: Automatically choose best mode based on task and resource type
    """

    VISUAL = "visual"  # Render as images for visual inspection
    DATA = "data"  # Raw data/text for analysis and manipulation
    NATIVE = "native"  # Native file format via API (PDFs, audio, video)
    AUTO = "auto"  # Choose best mode automatically


def get_default_mode_for_resource_type(
    mime_type: str,
    supports_native_files: bool = False,
) -> ResourceRepresentationMode:
    """Determine the best default representation mode for a resource type.

    Args:
        mime_type: MIME type of the resource
        supports_native_files: Whether the LLM API supports native file inputs

    Returns:
        Recommended representation mode
    """
    # Images: always visual
    if mime_type.startswith("image/"):
        return ResourceRepresentationMode.VISUAL

    # Spreadsheets: almost always want data for analysis
    if mime_type in [
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/vnd.ms-excel",
        "text/csv",
    ]:
        return ResourceRepresentationMode.DATA

    # PDFs: native if supported, else visual
    if mime_type == "application/pdf":
        if supports_native_files:
            return ResourceRepresentationMode.NATIVE
        return ResourceRepresentationMode.VISUAL

    # Audio/Video: native
    if mime_type.startswith(("audio/", "video/")):
        return ResourceRepresentationMode.NATIVE

    # Text: always data
    if mime_type.startswith("text/") or mime_type == "application/json":
        return ResourceRepresentationMode.DATA

    # Documents: visual for now (can add text extraction later)
    if mime_type in [
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/msword",
    ]:
        return ResourceRepresentationMode.VISUAL

    # Default: data
    return ResourceRepresentationMode.DATA

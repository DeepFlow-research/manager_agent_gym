"""Resource representation modes and utilities."""

from enum import Enum


class ResourceRepresentationMode(str, Enum):
    """Modes for representing resources to LLMs."""
    
    AUTO = "auto"  # Automatically choose best mode
    DATA = "data"  # Represent as structured data (markdown tables, text)
    VISUAL = "visual"  # Represent as images
    NATIVE = "native"  # Use native format if supported


def get_default_mode_for_resource_type(mime_type: str) -> ResourceRepresentationMode:
    """Get the default representation mode for a resource type.
    
    Args:
        mime_type: MIME type of the resource
        
    Returns:
        Default representation mode
    """
    if mime_type.startswith("image/"):
        return ResourceRepresentationMode.VISUAL
    elif mime_type in [
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/vnd.ms-excel",
        "text/csv",
    ]:
        # Excel/CSV: prefer structured data extraction
        return ResourceRepresentationMode.DATA
    elif mime_type == "application/pdf":
        # PDF: visual by default (images), but could be DATA for text extraction
        return ResourceRepresentationMode.VISUAL
    elif mime_type.startswith("text/"):
        return ResourceRepresentationMode.DATA
    else:
        return ResourceRepresentationMode.AUTO

"""
Resource data models for Manager Agent Gym.
"""

from pathlib import Path
from typing import Any, Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class Resource(BaseModel):
    """File-based workflow resource.

    All outputs are files: text (.md), data (.xlsx, .csv), documents (.pdf, .docx),
    media (.png, .mp4, .wav). No inline content - everything is stored on disk.

    This design enables:
    - Multimodal evaluation (visual inspection of documents, charts)
    - Direct file access in validation rules
    - Large file support without memory constraints
    - Tool interoperability (all tools work with files)

    Example:
        ```python
        # Markdown text resource
        Resource(
            name="Stakeholder Brief v1",
            description="Two-page summary for exec review",
            file_path="/tmp/workflow_xyz/brief_v1.md",
            mime_type="text/markdown",
            size_bytes=1024,
        )

        # Excel data resource
        Resource(
            name="Revenue Analysis Q4",
            description="Excel workbook with quarterly revenue breakdown",
            file_path="/tmp/workflow_xyz/revenue_q4.xlsx",
            mime_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            size_bytes=45120,
            file_format_metadata={
                "sheet_names": ["Summary", "Q1", "Q2", "Q3", "Q4"],
                "sheet_count": 5
            }
        )
        ```
    """

    id: UUID = Field(
        default_factory=uuid4, description="Unique identifier for the resource"
    )
    name: str = Field(
        ...,
        description="Human-readable resource name",
        examples=["Stakeholder Brief v1", "Revenue Analysis Q4"],
    )
    description: str = Field(
        ..., description="What this resource contains and how it is used"
    )

    # File storage (always present)
    file_path: str = Field(
        ...,
        description="Absolute path to resource file on disk",
    )
    mime_type: str = Field(
        ...,
        description="MIME type (e.g., text/markdown, application/pdf, application/vnd.openxmlformats-officedocument.spreadsheetml.sheet)",
        examples=[
            "text/markdown",
            "text/csv",
            "application/json",
            "application/pdf",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "image/png",
            "image/jpeg",
            "audio/wav",
            "audio/mpeg",
        ],
    )
    size_bytes: int = Field(
        ...,
        description="File size in bytes",
    )

    # Optional metadata
    file_format_metadata: dict[str, Any] | None = Field(
        default=None,
        description="Format-specific metadata (e.g., Excel: sheet names, PDF: page count, images: dimensions)",
    )

    # Resource flow control
    resource_role: Literal["output", "intermediary"] = Field(
        default="output",
        description="Whether this resource should be passed as input to dependent tasks. 'output' = final deliverable, 'intermediary' = temporary artifact.",
    )

    @property
    def resource_id(self) -> UUID:
        """Alias for id field to maintain compatibility."""
        return self.id

    @property
    def file_extension(self) -> str:
        """Get file extension (e.g., '.xlsx', '.md', '.pdf')"""
        return Path(self.file_path).suffix

    @property
    def is_text_format(self) -> bool:
        """Check if resource is text-based format (markdown, JSON, plain text)"""
        return self.mime_type.startswith(("text/", "application/json"))

    @property
    def is_document(self) -> bool:
        """Check if resource is a document (PDF, DOCX, etc.)"""
        return self.mime_type in [
            "application/pdf",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "application/msword",
        ]

    @property
    def is_spreadsheet(self) -> bool:
        """Check if resource is a spreadsheet (Excel, CSV)"""
        return self.mime_type in [
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "application/vnd.ms-excel",
            "text/csv",
        ]

    @property
    def is_image(self) -> bool:
        """Check if resource is an image"""
        return self.mime_type.startswith("image/")

    @property
    def is_audio(self) -> bool:
        """Check if resource is audio"""
        return self.mime_type.startswith("audio/")

    @property
    def is_video(self) -> bool:
        """Check if resource is video"""
        return self.mime_type.startswith("video/")

    def load_content(self) -> bytes:
        """
        Load file content as bytes.

        Returns:
            File content as bytes

        Raises:
            FileNotFoundError: If file does not exist
        """
        file_path = Path(self.file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {self.file_path}")

        return file_path.read_bytes()

    def load_text(self) -> str:
        """
        Load file content as text (for text-based formats).

        Returns:
            File content as string

        Raises:
            ValueError: If mime_type is not text-based
            FileNotFoundError: If file does not exist
        """
        if not self.is_text_format:
            raise ValueError(f"Cannot load text from non-text format: {self.mime_type}")

        file_path = Path(self.file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {self.file_path}")

        return file_path.read_text(encoding="utf-8")

    def save_to_file(self, content: bytes, file_path: str | Path) -> None:
        """
        Save binary content to a file and update resource metadata.

        Args:
            content: Binary content to save
            file_path: Destination path for the file
        """
        file_path = Path(file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_bytes(content)

        self.file_path = str(file_path.absolute())
        self.size_bytes = len(content)

    def pretty_print(self, max_preview_chars: int = 5000) -> str:
        """Return a human-readable summary of the resource."""
        lines: list[str] = []
        lines.append(
            f"Resource: {self.name} (ID: {self.id}, type={self.mime_type}, role={self.resource_role})"
        )
        if self.description:
            lines.append(f"  Description: {self.description}")

        lines.append(f"  File path: {self.file_path}")

        if self.size_bytes:
            size_kb = self.size_bytes / 1024
            lines.append(f"  Size: {size_kb:.2f} KB ({self.size_bytes} bytes)")

        if self.file_format_metadata:
            lines.append(f"  Metadata: {self.file_format_metadata}")

        # Show text preview for text files
        if self.is_text_format:
            try:
                text_content = self.load_text()
                word_count = len(text_content.split())
                char_len = len(text_content)
                lines.append(f"  Content stats: words={word_count}, chars={char_len}")

                preview = text_content[:max_preview_chars]
                if len(text_content) > max_preview_chars:
                    preview += "... (truncated)"
                lines.append("  Content preview:")
                for line in preview.splitlines()[:60]:
                    lines.append(f"    {line}")
            except Exception as e:
                lines.append(f"  Content: <unable to load: {e}>")

        return "\n".join(lines)

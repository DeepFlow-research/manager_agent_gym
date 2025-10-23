"""
Multimodal resource processing for agent inputs.

Converts Resource objects into OpenAI Responses API format for multimodal LLM consumption.
LiteLLM handles provider-specific format translation automatically.
"""

import base64
import tempfile
from pathlib import Path
from typing import Literal, cast

from openai.types.responses import (
    ResponseInputImageParam,
    ResponseInputTextParam,
)
from openai.types.responses.response_input_param import Message

from manager_agent_gym.schemas.domain.resource import Resource
from manager_agent_gym.core.common.logging import logger
from manager_agent_gym.core.common.resource_representation import (
    ResourceRepresentationMode,
    get_default_mode_for_resource_type,
)


class ResourceTokenEstimator:
    """Estimates token consumption for different resource types."""

    @staticmethod
    def estimate_tokens(
        resource: Resource,
        mode: ResourceRepresentationMode = ResourceRepresentationMode.AUTO,
    ) -> int:
        """Estimate token count for a resource.

        Args:
            resource: Resource to estimate tokens for
            mode: Representation mode to use

        Returns:
            Estimated token count
        """
        # Determine effective mode
        if mode == ResourceRepresentationMode.AUTO:
            mode = get_default_mode_for_resource_type(resource.mime_type)

        if resource.is_image:
            # Images: ~85-170 tokens per 512px tile in low detail
            # High detail: up to 1024 tokens per image (depends on size)
            # Conservative estimate: 1024 tokens per image
            return 1024

        elif resource.is_document:
            if mode == ResourceRepresentationMode.DATA:
                # PDF as text: estimate based on file size
                # Rough: 1 page = ~2KB text = ~500 tokens
                pages = (
                    resource.file_format_metadata.get("page_count", 1)
                    if resource.file_format_metadata
                    else 1
                )
                return min(int(pages) * 500, 5000)
            else:
                # PDF as images: 1024 tokens per page
                pages = (
                    resource.file_format_metadata.get("page_count", 1)
                    if resource.file_format_metadata
                    else 1
                )
                return min(int(pages) * 1024, 10240)

        elif resource.is_spreadsheet:
            if mode == ResourceRepresentationMode.DATA:
                # Excel as markdown tables: much cheaper!
                # Estimate: 100 rows × 6 columns × 10 chars/cell ÷ 4 = ~1500 tokens per sheet
                sheet_count = (
                    resource.file_format_metadata.get("sheet_count", 1)
                    if resource.file_format_metadata
                    else 1
                )
                return min(int(sheet_count) * 1500, 7500)
            else:
                # Excel as images: 1024 tokens per sheet
                sheet_count = (
                    resource.file_format_metadata.get("sheet_count", 1)
                    if resource.file_format_metadata
                    else 1
                )
                return min(int(sheet_count) * 1024, 10240)

        elif resource.is_text_format:
            # Text: ~4 chars per token (rough estimate)
            try:
                text = resource.load_text()
                return len(text) // 4
            except Exception:
                return 0

        else:
            # Unknown type: assume minimal tokens
            return 100


def encode_image_to_base64(image_path: str | Path) -> str:
    """Encode an image file to base64 string.

    Args:
        image_path: Path to image file

    Returns:
        Base64-encoded image string (without data URL prefix)
    """
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


def create_text_content(text: str) -> ResponseInputTextParam:
    """Create strongly-typed text content for OpenAI Responses API.

    Args:
        text: Text content

    Returns:
        Typed text parameter
    """
    return ResponseInputTextParam(type="input_text", text=text)


def create_image_content(
    image_url_or_b64: str,
    detail: Literal["auto", "low", "high"] = "high",
    is_base64: bool = False,
    mime_type: str = "image/jpeg",
) -> ResponseInputImageParam:
    """Create strongly-typed image content for OpenAI Responses API.

    Args:
        image_url_or_b64: Either a URL or base64-encoded image data
        detail: Detail level - "high" for detailed analysis, "low" for faster/cheaper
        is_base64: Whether the input is base64-encoded data
        mime_type: MIME type of the image

    Returns:
        Typed image parameter
    """
    if is_base64:
        image_url = f"data:{mime_type};base64,{image_url_or_b64}"
    else:
        image_url = image_url_or_b64

    return ResponseInputImageParam(
        type="input_image",
        image_url=image_url,
        detail=detail,
    )


def create_user_message(
    *content_parts: ResponseInputTextParam | ResponseInputImageParam | str,
) -> Message:
    """Create a strongly-typed user message with mixed content.

    Args:
        *content_parts: Text and/or image content parts (strings auto-converted to text)

    Returns:
        Typed message object
    """
    # Convert string inputs to text content
    typed_parts: list[ResponseInputTextParam | ResponseInputImageParam] = []
    for part in content_parts:
        if isinstance(part, str):
            typed_parts.append(create_text_content(part))
        else:
            typed_parts.append(part)

    if not typed_parts:
        typed_parts = [create_text_content("")]

    # Cast to Message content format - OpenAI types are complex unions
    return Message(
        type="message",
        role="user",
        content=cast(
            "list[ResponseInputTextParam | ResponseInputImageParam]", typed_parts
        ),  # type: ignore[arg-type]
    )


class MultimodalResourceProcessor:
    """Processes Resource objects into multimodal LLM inputs.

    Handles conversion of images, PDFs, Excel files, and text into
    OpenAI Responses API format. LiteLLM translates to provider-specific
    formats automatically.
    """

    def __init__(
        self,
        max_tokens: int | None = 100000,
        default_image_detail: Literal["auto", "low", "high"] = "high",
        representation_mode: ResourceRepresentationMode = ResourceRepresentationMode.AUTO,
    ):
        """Initialize processor.

        Args:
            max_tokens: Maximum tokens to use for resources (None = unlimited)
            default_image_detail: Default detail level for images
            representation_mode: How to represent resources (AUTO, DATA, VISUAL, NATIVE)
        """
        self.max_tokens = max_tokens
        self.default_image_detail = default_image_detail
        self.representation_mode = representation_mode
        self.estimator = ResourceTokenEstimator()

    async def format_resources_as_content(
        self,
        resources: list[Resource],
        include_metadata: bool = True,
    ) -> list[ResponseInputTextParam | ResponseInputImageParam]:
        """Convert resources to multimodal content blocks.

        Args:
            resources: List of resources to format
            include_metadata: Whether to include text metadata about resources

        Returns:
            List of content blocks (text + images) ready for LLM
        """
        if not resources:
            return [create_text_content("No input resources provided.")]

        # Estimate total tokens
        total_tokens = sum(
            self.estimator.estimate_tokens(r, self.representation_mode)
            for r in resources
        )

        # Check if we need to truncate
        if self.max_tokens and total_tokens > self.max_tokens:
            logger.warning(
                f"Resources exceed token limit ({total_tokens} > {self.max_tokens}). "
                "Applying truncation strategy."
            )
            return await self._format_with_truncation(resources, include_metadata)

        # Format all resources
        return await self._format_all_resources(resources, include_metadata)

    async def _format_all_resources(
        self,
        resources: list[Resource],
        include_metadata: bool,
    ) -> list[ResponseInputTextParam | ResponseInputImageParam]:
        """Format all resources without truncation."""
        content_blocks: list[ResponseInputTextParam | ResponseInputImageParam] = []

        for idx, resource in enumerate(resources, 1):
            # Add metadata header
            if include_metadata:
                header = f"\n--- Resource {idx}: {resource.name} ---\n"
                header += f"Description: {resource.description}\n"
                header += f"Type: {resource.mime_type}\n"
                header += f"File path: {resource.file_path}\n"
                content_blocks.append(create_text_content(header))

            # Add resource content
            try:
                resource_content = await self._format_single_resource(resource)
                content_blocks.extend(resource_content)
            except Exception as e:
                logger.error(f"Error formatting resource {resource.name}: {e}")
                content_blocks.append(
                    create_text_content(f"(Error loading resource: {str(e)})")
                )

        return content_blocks

    def _determine_mode_for_resource(
        self, resource: Resource
    ) -> ResourceRepresentationMode:
        """Determine the effective representation mode for a resource.

        Args:
            resource: Resource to determine mode for

        Returns:
            Effective representation mode
        """
        if self.representation_mode != ResourceRepresentationMode.AUTO:
            return self.representation_mode

        # AUTO mode: choose best based on resource type
        return get_default_mode_for_resource_type(resource.mime_type)

    async def _format_single_resource(
        self,
        resource: Resource,
    ) -> list[ResponseInputTextParam | ResponseInputImageParam]:
        """Format a single resource into content blocks.

        Args:
            resource: Resource to format

        Returns:
            List of content blocks for this resource
        """
        # Determine effective mode
        mode = self._determine_mode_for_resource(resource)

        if resource.is_image:
            return await self._format_image(resource)

        elif resource.is_document:
            return await self._format_pdf(resource)

        elif resource.is_spreadsheet:
            # Choose formatting based on mode
            if mode == ResourceRepresentationMode.DATA:
                return await self._format_excel_as_data(resource)
            else:
                return await self._format_excel(resource)

        elif resource.is_text_format:
            return self._format_text(resource)

        else:
            return [
                create_text_content(
                    f"(Unsupported resource type: {resource.mime_type})"
                )
            ]

    async def _format_image(
        self,
        resource: Resource,
    ) -> list[ResponseInputTextParam | ResponseInputImageParam]:
        """Format an image resource.

        Args:
            resource: Image resource

        Returns:
            List containing image content block
        """
        # Encode image to base64
        image_b64 = encode_image_to_base64(resource.file_path)

        # Determine MIME type from resource
        mime_type = resource.mime_type

        # Ensure detail level is properly typed
        detail: Literal["auto", "low", "high"] = self.default_image_detail  # type: ignore[assignment]

        return [
            create_image_content(
                image_b64,
                detail=detail,
                is_base64=True,
                mime_type=mime_type,
            )
        ]

    async def _format_pdf(
        self,
        resource: Resource,
        max_pages: int = 10,
    ) -> list[ResponseInputTextParam | ResponseInputImageParam]:
        """Format a PDF resource by converting to images.

        Args:
            resource: PDF resource
            max_pages: Maximum pages to include

        Returns:
            List of content blocks (text + images for each page)
        """
        try:
            import fitz  # type: ignore  # PyMuPDF

            doc = fitz.open(resource.file_path)
            content_blocks: list[ResponseInputTextParam | ResponseInputImageParam] = []

            # Create temp directory for page images
            temp_dir = Path(tempfile.mkdtemp(prefix="pdf_pages_"))

            num_pages = min(len(doc), max_pages)
            for page_num in range(num_pages):
                page = doc[page_num]
                # Render at 150 DPI for good quality
                pix = page.get_pixmap(dpi=150)
                img_path = temp_dir / f"page_{page_num:03d}.png"
                pix.save(str(img_path))

                # Add page label
                content_blocks.append(create_text_content(f"\nPage {page_num + 1}:"))

                # Add page image
                image_b64 = encode_image_to_base64(img_path)
                detail: Literal["auto", "low", "high"] = self.default_image_detail  # type: ignore[assignment]
                content_blocks.append(
                    create_image_content(
                        image_b64,
                        detail=detail,
                        is_base64=True,
                        mime_type="image/png",
                    )
                )

            doc.close()

            if len(doc) > max_pages:
                content_blocks.append(
                    create_text_content(
                        f"\n(Showing first {max_pages} of {len(doc)} pages)"
                    )
                )

            return content_blocks

        except ImportError:
            logger.warning("PyMuPDF not installed, cannot render PDF pages")
            return [
                create_text_content(
                    "(PDF rendering not available - install PyMuPDF to enable)"
                )
            ]
        except Exception as e:
            logger.error(f"Error rendering PDF: {e}")
            return [create_text_content(f"(Error rendering PDF: {str(e)})")]

    async def _format_excel(
        self,
        resource: Resource,
        max_sheets: int = 10,
    ) -> list[ResponseInputTextParam | ResponseInputImageParam]:
        """Format an Excel resource by rendering sheets as images.

        Args:
            resource: Excel resource
            max_sheets: Maximum sheets to include

        Returns:
            List of content blocks (text + images for each sheet)
        """
        try:
            import pandas as pd  # type: ignore
            import matplotlib  # type: ignore

            matplotlib.use("Agg")
            import matplotlib.pyplot as plt

            temp_dir = Path(tempfile.mkdtemp(prefix="excel_sheets_"))
            content_blocks: list[ResponseInputTextParam | ResponseInputImageParam] = []

            xls = pd.ExcelFile(resource.file_path)
            sheet_names = xls.sheet_names[:max_sheets]

            for sheet_name in sheet_names:
                df = pd.read_excel(xls, sheet_name=sheet_name)

                # Limit rows for visualization
                if len(df) > 100:
                    df_display = df.head(100)
                    truncated = True
                else:
                    df_display = df
                    truncated = False

                # Create figure
                fig, ax = plt.subplots(figsize=(14, max(8, len(df_display) * 0.3)))
                ax.axis("tight")
                ax.axis("off")

                # Add title
                title = f"Sheet: {sheet_name}"
                if truncated:
                    title += f" (showing first 100 of {len(df)} rows)"
                plt.title(title, fontsize=12, pad=20)

                # Create table
                table_data = df_display.values.tolist()
                col_labels = df_display.columns.tolist()

                table = ax.table(
                    cellText=table_data,
                    colLabels=col_labels,
                    loc="center",
                    cellLoc="left",
                )
                table.auto_set_font_size(False)
                table.set_fontsize(8)
                table.scale(1, 1.5)

                # Style header
                for j in range(len(col_labels)):
                    cell = table[(0, j)]
                    cell.set_facecolor("#4472C4")
                    cell.set_text_props(weight="bold", color="white")

                # Save to file
                img_path = temp_dir / f"sheet_{sheet_name.replace('/', '_')}.png"
                plt.savefig(str(img_path), bbox_inches="tight", dpi=150)
                plt.close()

                # Add to content blocks
                content_blocks.append(create_text_content(f"\nSheet: {sheet_name}"))

                image_b64 = encode_image_to_base64(img_path)
                detail: Literal["auto", "low", "high"] = self.default_image_detail  # type: ignore[assignment]
                content_blocks.append(
                    create_image_content(
                        image_b64,
                        detail=detail,
                        is_base64=True,
                        mime_type="image/png",
                    )
                )

            if len(xls.sheet_names) > max_sheets:
                content_blocks.append(
                    create_text_content(
                        f"\n(Showing first {max_sheets} of {len(xls.sheet_names)} sheets)"
                    )
                )

            return content_blocks

        except ImportError:
            logger.warning(
                "pandas/matplotlib not installed, cannot render Excel sheets"
            )
            return [
                create_text_content(
                    "(Excel rendering not available - install pandas and matplotlib to enable)"
                )
            ]
        except Exception as e:
            logger.error(f"Error rendering Excel: {e}")
            return [create_text_content(f"(Error rendering Excel: {str(e)})")]

    async def _format_excel_as_data(
        self,
        resource: Resource,
        max_rows_per_sheet: int = 100,
        max_sheets: int = 10,
    ) -> list[ResponseInputTextParam | ResponseInputImageParam]:
        """Format an Excel resource as markdown tables for data analysis.

        This is much more token-efficient than rendering as images and allows
        the LLM to directly work with the data.

        Args:
            resource: Excel resource
            max_rows_per_sheet: Maximum rows to include per sheet
            max_sheets: Maximum sheets to include

        Returns:
            List of text content blocks with markdown tables
        """
        try:
            import pandas as pd  # type: ignore

            content_blocks: list[ResponseInputTextParam | ResponseInputImageParam] = []

            # Read Excel file
            if resource.mime_type == "text/csv":
                # CSV file - single sheet
                df = pd.read_csv(resource.file_path)
                sheet_names = ["CSV"]
                dfs = {"CSV": df}
            else:
                # Excel file - multiple sheets
                xls = pd.ExcelFile(resource.file_path)
                sheet_names = xls.sheet_names[:max_sheets]
                dfs = {
                    name: pd.read_excel(xls, sheet_name=name) for name in sheet_names
                }

            for sheet_name in sheet_names:
                df = dfs[sheet_name]

                # Create header
                text_parts = [f"\nSheet: {sheet_name}"]

                if len(df) > max_rows_per_sheet:
                    text_parts.append(
                        f"(Showing first {max_rows_per_sheet} of {len(df)} rows)"
                    )
                    df_display = df.head(max_rows_per_sheet)
                else:
                    df_display = df

                # Convert to markdown table
                try:
                    # Replace NaN with empty string for cleaner display
                    df_display = df_display.fillna("")

                    # Create markdown table
                    table_md = df_display.to_markdown(index=False)

                    text_parts.append(f"\n{table_md}\n")

                    # Add summary stats if numeric columns exist
                    numeric_cols = df_display.select_dtypes(include=["number"]).columns
                    if len(numeric_cols) > 0:
                        text_parts.append(f"(Total rows in sheet: {len(df)})")

                except Exception as e:
                    logger.warning(
                        f"Could not create markdown table for {sheet_name}: {e}"
                    )
                    # Fallback: show column names and first few rows as text
                    text_parts.append(
                        f"\nColumns: {', '.join(df_display.columns.tolist())}"
                    )
                    text_parts.append(
                        f"\nFirst few rows:\n{df_display.head(5).to_string()}"
                    )

                content_blocks.append(create_text_content("\n".join(text_parts)))

            # Add truncation notice if needed
            if resource.mime_type != "text/csv":
                xls = pd.ExcelFile(resource.file_path)
                if len(xls.sheet_names) > max_sheets:
                    content_blocks.append(
                        create_text_content(
                            f"\n(Showing first {max_sheets} of {len(xls.sheet_names)} sheets)"
                        )
                    )

            return content_blocks

        except ImportError:
            logger.warning("pandas not installed, falling back to visual rendering")
            # Fallback to visual rendering
            return await self._format_excel(resource)
        except Exception as e:
            logger.error(f"Error formatting Excel as data: {e}")
            return [create_text_content(f"(Error formatting Excel: {str(e)})")]

    def _format_text(
        self,
        resource: Resource,
        max_chars: int = 50000,
    ) -> list[ResponseInputTextParam | ResponseInputImageParam]:
        """Format a text resource.

        Args:
            resource: Text resource
            max_chars: Maximum characters to include

        Returns:
            List containing text content block
        """
        try:
            text = resource.load_text()

            if len(text) > max_chars:
                text = (
                    text[:max_chars]
                    + f"\n\n... (truncated, showing first {max_chars} chars)"
                )

            return [create_text_content(f"\nContent:\n{text}")]

        except Exception as e:
            logger.error(f"Error loading text: {e}")
            return [create_text_content(f"(Error loading text: {str(e)})")]

    async def _format_with_truncation(
        self,
        resources: list[Resource],
        include_metadata: bool,
    ) -> list[ResponseInputTextParam | ResponseInputImageParam]:
        """Format resources with truncation when exceeding token limit.

        Uses "first N resources" strategy - includes resources until token limit.
        """
        content_blocks: list[ResponseInputTextParam | ResponseInputImageParam] = []
        tokens_used = 0
        resources_included = 0

        for idx, resource in enumerate(resources, 1):
            resource_tokens = self.estimator.estimate_tokens(
                resource, self.representation_mode
            )

            if self.max_tokens and (tokens_used + resource_tokens) > self.max_tokens:
                # Would exceed limit - stop here
                break

            # Add this resource
            if include_metadata:
                header = f"\n--- Resource {idx}: {resource.name} ---\n"
                header += f"Description: {resource.description}\n"
                header += f"Type: {resource.mime_type}\n"
                header += f"File path: {resource.file_path}\n"
                content_blocks.append(create_text_content(header))

            try:
                resource_content = await self._format_single_resource(resource)
                content_blocks.extend(resource_content)
                tokens_used += resource_tokens
                resources_included += 1
            except Exception as e:
                logger.error(f"Error formatting resource {resource.name}: {e}")
                content_blocks.append(
                    create_text_content(f"(Error loading resource: {str(e)})")
                )

        # Add truncation notice
        if resources_included < len(resources):
            content_blocks.append(
                create_text_content(
                    f"\n⚠️ Truncated: Showing {resources_included} of {len(resources)} resources "
                    f"(token limit: {self.max_tokens})"
                )
            )

        return content_blocks

"""
Multimodal LLM evaluation engine using GPT-4 Vision.

Enables single-call evaluation of documents, spreadsheets, images, and text
by preprocessing files into multimodal prompts.
"""

import base64
import logging
import os
import tempfile
from pathlib import Path
from typing import Any

import instructor
from openai import AsyncOpenAI
from pydantic import BaseModel, Field

from manager_agent_gym.schemas.domain.resource import Resource

logger = logging.getLogger(__name__)


class _MultimodalLLMResponse(BaseModel):
    """Internal: Structured response format for multimodal LLM evaluation.

    This is a private class used only for parsing GPT-4 Vision responses.
    Not to be confused with the public EvaluationResult in preferences.evaluation.
    """

    score: float = Field(
        description="Numerical score for the evaluation (0.0 to max_score)"
    )
    reasoning: str = Field(
        description="Detailed explanation of the score, citing specific evidence from the outputs"
    )


class MultimodalEvaluator:
    """GPT-4 Vision-based evaluator for documents, charts, formatting.

    Converts various file types (PDF, Excel, images) into a single multimodal
    prompt for GPT-4 Vision to evaluate.
    """

    def __init__(self, client: AsyncOpenAI | None = None):
        """
        Initialize evaluator.

        Args:
            client: OpenAI async client (creates default if None)
        """
        # Create base OpenAI client
        base_client = client or AsyncOpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        self.client = base_client
        # Patch with Instructor for structured outputs
        self.instructor_client = instructor.from_openai(base_client)

    async def evaluate_with_vision(
        self,
        prompt: str,
        resources: list[Resource],
        max_score: float = 1.0,
        model: str = "gpt-5",
    ) -> tuple[float, str]:
        """
        Single LLM call with multimodal context.

        Preprocesses files into text/images and sends to GPT-4 Vision.

        Args:
            prompt: Evaluation prompt (rubric criteria)
            resources: Resources to evaluate (PDFs, Excel, images, text)
            max_score: Maximum score for normalization
            model: OpenAI model to use (defaults to gpt-4o-2024-11-20, must support vision)

        Returns:
            (score, reasoning) tuple
        """
        logger.info(f"Evaluating {len(resources)} resources with multimodal LLM")

        # Log detailed resource information
        for idx, resource in enumerate(resources):
            logger.info(
                f"Starting evaluation of {len(resources)} resources with multimodal LLM"
                f"  Resource {idx + 1}/{len(resources)}: "
                f"name='{resource.name}', "
                f"mime_type={resource.mime_type}, "
                f"file_path={resource.file_path}, "
                f"size={resource.size_bytes} bytes"
            )

        # Prepare multimodal content
        content: list[dict[str, Any]] = [
            {
                "type": "text",
                "text": f"Evaluation Criteria:\n\n{prompt}\n\nPlease evaluate the following outputs:",
            }
        ]

        for idx, resource in enumerate(resources):
            # Include resource role to help evaluator distinguish outputs from intermediaries
            role_label = resource.resource_role or "output"
            content.append(
                {
                    "type": "text",
                    "text": f"\n\n--- Resource {idx + 1}: {resource.name} (role: {role_label}) ---",
                }
            )

            try:
                if resource.is_image:
                    # Direct image
                    content.append(self._image_content(resource.file_path))

                elif resource.is_document:
                    # Convert PDF pages to images
                    images = self._pdf_to_images(resource.file_path)
                    for page_num, img_path in enumerate(
                        images[:10], 1
                    ):  # Limit to first 10 pages
                        content.append({"type": "text", "text": f"Page {page_num}:"})
                        content.append(self._image_content(img_path))

                elif resource.is_spreadsheet:
                    # Render Excel as images (charts + tables)
                    images = self._excel_to_images(resource.file_path)
                    for sheet_num, img_path in enumerate(images, 1):
                        content.append({"type": "text", "text": f"Sheet {sheet_num}:"})
                        content.append(self._image_content(img_path))

                elif resource.is_text_format:
                    # Include text directly
                    text = Path(resource.file_path).read_text(encoding="utf-8")
                    content.append({"type": "text", "text": f"\n{text}\n"})

                else:
                    content.append(
                        {
                            "type": "text",
                            "text": f"(Unsupported file type: {resource.mime_type})",
                        }
                    )

            except Exception as e:
                logger.error(f"Error processing resource {resource.name}: {e}")
                content.append(
                    {"type": "text", "text": f"(Error loading resource: {str(e)})"}
                )

        # Add scoring instruction
        content.append(
            {
                "type": "text",
                "text": f"\n\nProvide your evaluation with a score between 0.0 and {max_score}, along with detailed reasoning citing specific evidence.",
            }
        )

        # Single LLM call with structured output
        try:
            system_prompt = f"""You are an LLM judge evaluating task output artifacts against structured rubric criteria.

Definition and setting:
- Task outputs in this system are multimodal resources (Excel files, PDFs, Markdown reports, images) produced by AI agents completing workflow tasks.
- You will be shown the FULL CONTENT of all output resources: PDFs as images, Excel sheets as rendered tables, text/markdown directly, etc.
- Each resource is labeled with its role: "output" (final deliverable) or "intermediary" (working file/process artifact).

Evaluation framing:
- Your job is to assess how well the artifacts meet specific quality criteria defined in the EVALUATION CRITERIA below (treat it as a detailed rubric).
- The criteria may cover structure, correctness, formatting, completeness, professionalism, or other aspects.
- **CRITICAL**: Focus your evaluation on resources marked with role="output" (the final deliverables). Intermediary files are shown for context only.
  - For FORMAT/STRUCTURE checks: Only evaluate final outputs (role="output"). Intermediary files are part of the process and should NOT be critiqued for format issues.
  - For QUALITY/CORRECTNESS checks: Use intermediary files as supporting evidence if helpful, but score based on the final outputs.
  - If the criteria explicitly mentions "process" or "working files", then consider intermediaries; otherwise, focus on final outputs.

Instructions:
- Carefully read the EVALUATION CRITERIA and operationalize them as checkable conditions.
- Examine ALL provided resources thoroughly. Cross-reference between files when needed (e.g., check if Excel data matches report descriptions).
- Use ONLY the visible artifacts as evidence. If evidence is missing or inconclusive, state that explicitly and score conservatively.
- In your reasoning, cite SPECIFIC evidence from the resources (e.g., "Sheet 'Summary' row 5 shows...", "Section 2.3 states...", "Chart on page 2 displays...").
- Provide actionable feedback: what's missing, what's incorrect, or what could be improved.

Scoring guide (apply these rules uniformly):
- 0: No relevant evidence, contradictory evidence, or explicit failures against the criteria.
- 0.25×max_score: Minimal evidence or weak/indirect signals; at most one element satisfied with major gaps.
- 0.5×max_score: Partial fulfillment; roughly half of the required elements satisfied with cited evidence; notable gaps remain.
- 0.75×max_score: Strong fulfillment; most elements satisfied with high-quality evidence; only minor gaps.
- {max_score} (maximum): Complete fulfillment across all required elements with explicit, verifiable citations and evidence.

Partial-credit rules when criteria enumerate elements (e.g., items 1-5 or bullet lists):
- Divide the maximum score evenly across the N enumerated elements.
- For each element: award 0 for absent/contradictory, 0.5 of the element share for incomplete/weak evidence, 1.0 of the element share for clear satisfaction.
- If evidence is entirely missing for the criterion, cap total at 0.5×max_score.
- If there is contradictory evidence, reduce total by at least 0.25×max_score (not below 0).

Be thorough, evidence-based, and fair. Quality evaluations require attention to detail."""

            result: _MultimodalLLMResponse = (
                await self.instructor_client.chat.completions.create(
                    model=model,
                    messages=[
                        {
                            "role": "system",
                            "content": system_prompt,
                        },
                        {
                            "role": "user",
                            "content": content,  # type: ignore
                        },
                    ],
                    response_model=_MultimodalLLMResponse,
                    max_completion_tokens=5000,
                    temperature=1.0,
                )
            )

            # Clamp score to valid range
            score = max(0.0, min(result.score, max_score))

            logger.info(f"Multimodal evaluation complete: {score}/{max_score}")
            return score, result.reasoning

        except Exception as e:
            logger.error(f"Multimodal evaluation failed: {e}")
            return 0.0, f"Evaluation error: {str(e)}"

    def _image_content(self, image_path: str) -> dict[str, Any]:
        """
        Create image content for API.

        Args:
            image_path: Path to image file

        Returns:
            Image content dict for OpenAI API
        """
        with open(image_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()

        # Detect image format
        suffix = Path(image_path).suffix.lower()
        if suffix == ".png":
            mime = "image/png"
        elif suffix in [".jpg", ".jpeg"]:
            mime = "image/jpeg"
        elif suffix == ".gif":
            mime = "image/gif"
        elif suffix == ".webp":
            mime = "image/webp"
        else:
            mime = "image/png"  # Default

        return {
            "type": "image_url",
            "image_url": {
                "url": f"data:{mime};base64,{b64}",
                "detail": "high",  # Request high-res analysis
            },
        }

    def _pdf_to_images(self, pdf_path: str) -> list[str]:
        """
        Convert PDF pages to PNG images.

        Args:
            pdf_path: Path to PDF file

        Returns:
            List of paths to generated PNG files
        """
        try:
            import fitz  # type: ignore  # PyMuPDF

            doc = fitz.open(pdf_path)
            images = []

            temp_dir = Path(tempfile.mkdtemp(prefix="pdf_eval_"))

            for page_num in range(len(doc)):
                page = doc[page_num]
                # Render at 150 DPI for good quality
                pix = page.get_pixmap(dpi=150)
                img_path = temp_dir / f"page_{page_num:03d}.png"
                pix.save(str(img_path))
                images.append(str(img_path))

            doc.close()
            return images

        except ImportError:
            logger.warning("PyMuPDF not installed, cannot convert PDF to images")
            return []
        except Exception as e:
            logger.error(f"Error converting PDF to images: {e}")
            return []

    def _excel_to_images(self, excel_path: str) -> list[str]:
        """
        Render Excel sheets as images (for visual inspection).

        Args:
            excel_path: Path to Excel file

        Returns:
            List of paths to generated PNG files
        """
        try:
            import pandas as pd  # type: ignore
            import matplotlib

            matplotlib.use("Agg")  # Use non-interactive backend
            import matplotlib.pyplot as plt

            temp_dir = Path(tempfile.mkdtemp(prefix="excel_eval_"))
            images = []

            try:
                xls = pd.ExcelFile(excel_path)
            except Exception as e:
                logger.error(f"Could not read Excel file: {e}")
                return []

            for sheet_name in xls.sheet_names[:10]:  # Limit to 10 sheets
                try:
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

                    img_path = temp_dir / f"sheet_{sheet_name.replace('/', '_')}.png"
                    plt.savefig(str(img_path), bbox_inches="tight", dpi=150)
                    plt.close()
                    images.append(str(img_path))

                except Exception as e:
                    logger.warning(f"Could not render sheet '{sheet_name}': {e}")
                    continue

            return images

        except ImportError:
            logger.warning("pandas/matplotlib not installed, cannot render Excel")
            return []
        except Exception as e:
            logger.error(f"Error rendering Excel to images: {e}")
            return []

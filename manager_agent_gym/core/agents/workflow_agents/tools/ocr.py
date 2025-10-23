"""OCR tools (image and PDF text extraction) - two-layer architecture."""

import json
from io import BytesIO
from pathlib import Path
from typing import TYPE_CHECKING, Any

import fitz
import pytesseract
from agents import Tool, function_tool
from PIL import Image

if TYPE_CHECKING:
    from manager_agent_gym.core.workflow.resource_storage import ResourceFileManager


# ============================================================================
# LAYER 1: OCR OPERATIONS (Core Business Logic)
# ============================================================================


async def _extract_text_from_image(
    file_path: str, language: str = "eng"
) -> dict[str, Any]:
    """Extract text from image using OCR."""
    try:
        file_path_obj = Path(file_path)
        if not file_path_obj.exists():
            return {"success": False, "error": "Image file not found"}

        image = Image.open(file_path)
        text = pytesseract.image_to_string(image, lang=language)

        if not text.strip():
            return {"success": True, "text": "", "warning": "No text extracted"}

        return {"success": True, "text": text}

    except Exception as e:
        error_msg = str(e)
        if "tesseract is not installed" in error_msg.lower():
            return {
                "success": False,
                "error": "Tesseract OCR not installed. See: https://github.com/tesseract-ocr/tesseract",
            }
        return {"success": False, "error": f"Error: {error_msg}"}


async def _extract_text_from_pdf_images(
    file_path: str, language: str = "eng"
) -> dict[str, Any]:
    """Extract text from scanned PDF pages using OCR."""
    try:
        file_path_obj = Path(file_path)
        if not file_path_obj.exists():
            return {"success": False, "error": "PDF file not found"}

        pdf_document = fitz.open(file_path)
        pages_text = []

        for page_num in range(len(pdf_document)):
            page = pdf_document[page_num]
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
            img_data = pix.tobytes("png")
            image = Image.open(BytesIO(img_data))
            text = pytesseract.image_to_string(image, lang=language)

            pages_text.append(
                {
                    "page": page_num + 1,
                    "text": text.strip(),
                    "has_text": bool(text.strip()),
                }
            )

        pdf_document.close()

        return {
            "success": True,
            "file_path": str(file_path),
            "total_pages": len(pages_text),
            "pages": pages_text,
        }

    except Exception as e:
        return {"success": False, "error": f"Error: {str(e)}"}


async def _get_image_text_confidence(
    file_path: str, language: str = "eng"
) -> dict[str, Any]:
    """Extract text with confidence scores from image."""
    try:
        file_path_obj = Path(file_path)
        if not file_path_obj.exists():
            return {"success": False, "error": "Image file not found"}

        image = Image.open(file_path)
        ocr_data = pytesseract.image_to_data(
            image, lang=language, output_type=pytesseract.Output.DICT
        )

        results = []
        for i in range(len(ocr_data["text"])):
            text = ocr_data["text"][i].strip()
            if text:
                results.append(
                    {"text": text, "confidence": ocr_data["conf"][i], "word_num": i}
                )

        avg_confidence = (
            sum(r["confidence"] for r in results) / len(results) if results else 0
        )

        return {
            "success": True,
            "file_path": str(file_path),
            "total_words": len(results),
            "words": results,
            "average_confidence": avg_confidence,
        }

    except Exception as e:
        return {"success": False, "error": f"Error: {str(e)}"}


# ============================================================================
# LAYER 2: OPENAI TOOL WRAPPERS
# ============================================================================


def create_ocr_tools(resource_manager: "ResourceFileManager") -> list[Tool]:
    """Create OCR tools for OpenAI SDK."""

    @function_tool
    async def extract_text_from_image(file_path: str, language: str = "eng") -> str:
        """
        Extract text content from images using Optical Character Recognition (OCR).

        This tool uses Tesseract OCR to extract text from image files including photos,
        screenshots, scanned documents, or any image containing text. Supports multiple
        languages and works with various image formats (PNG, JPG, TIFF, etc.). Perfect
        for digitizing printed text or extracting text from visual content.

        Note: Requires Tesseract OCR to be installed on the system.

        Parameters:
            file_path (str):
                The path to the image file to process.
                Example: "/path/to/image.png" or "scans/document.jpg"
            language (str):
                The language code for OCR processing. Common codes:
                - "eng" for English (default)
                - "spa" for Spanish
                - "fra" for French
                - "deu" for German
                - "chi_sim" for Simplified Chinese
                Default: "eng"

        Returns:
            str:
                The extracted text from the image, or an error message if OCR fails
                (e.g., Tesseract not installed, file not found, no text detected).

        Usage:
            Call this tool when you need to extract text from images. Common uses include:
            reading scanned documents, extracting text from screenshots, digitizing printed
            materials, or processing photos containing text like signs or labels.
        """
        result = await _extract_text_from_image(file_path, language)
        if result["success"]:
            return result["text"]
        return f"Error: {result.get('error')}"

    @function_tool
    async def extract_text_from_pdf_images(
        file_path: str, language: str = "eng"
    ) -> str:
        """
        Extract text from scanned or image-based PDF files using OCR technology.

        This tool processes PDF files that contain images or scanned pages (not text PDFs)
        and extracts text from each page using OCR. Each page is converted to an image
        and processed separately. Perfect for digitizing scanned documents, old PDFs,
        or image-based PDF files. For text-based PDFs, use the regular read_pdf tool instead.

        Note: Requires Tesseract OCR and PyMuPDF to be installed.

        Parameters:
            file_path (str):
                The path to the scanned/image-based PDF file.
                Example: "/path/to/scanned_document.pdf"
            language (str):
                The language code for OCR processing. Common codes:
                - "eng" for English (default)
                - "spa" for Spanish
                - "fra" for French
                Use the same codes as Tesseract OCR supports.
                Default: "eng"

        Returns:
            str:
                JSON string containing:
                - success: Whether the operation succeeded
                - file_path: Path to the processed file
                - total_pages: Number of pages processed
                - pages: Array of page results, each containing:
                  * page: Page number
                  * text: Extracted text from that page
                  * has_text: Whether text was found on the page

        Usage:
            Use this tool for scanned PDFs or image-based PDFs where regular PDF text
            extraction doesn't work. Common uses include: processing scanned documents,
            digitizing old records, extracting text from PDF images, or handling PDFs
            created from photos or scans.
        """
        result = await _extract_text_from_pdf_images(file_path, language)
        return json.dumps(result, indent=2)

    @function_tool
    async def get_image_text_confidence(file_path: str, language: str = "eng") -> str:
        """
        Extract text from images with detailed confidence scores for quality assessment.

        This tool performs OCR on images and returns not just the text, but also confidence
        scores for each word extracted. The confidence scores (0-100) indicate how certain
        the OCR engine is about each word's accuracy. Perfect for quality control, validating
        OCR results, or filtering unreliable text extractions.

        Note: Requires Tesseract OCR to be installed on the system.

        Parameters:
            file_path (str):
                The path to the image file to analyze.
                Example: "/path/to/image.png"
            language (str):
                The language code for OCR processing (e.g., "eng", "spa", "fra").
                Default: "eng"

        Returns:
            str:
                JSON string containing:
                - success: Whether the operation succeeded
                - file_path: Path to the processed file
                - total_words: Number of words detected
                - words: Array of word objects, each containing:
                  * text: The extracted word
                  * confidence: Confidence score (0-100, higher is better)
                  * word_num: Position index of the word
                - average_confidence: Overall average confidence score for the entire image

        Usage:
            Use this tool when you need to assess OCR quality or filter results by confidence.
            Common uses include: validating OCR accuracy, identifying low-quality extractions,
            quality control for scanned documents, or determining if an image needs manual
            review based on confidence scores.
        """
        result = await _get_image_text_confidence(file_path, language)
        return json.dumps(result, indent=2)

    return [
        extract_text_from_image,
        extract_text_from_pdf_images,
        get_image_text_confidence,
    ]

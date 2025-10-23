"""Comprehensive tests for OCR tools.

Tests image and PDF OCR operations.
"""

from pathlib import Path

import pytest

from manager_agent_gym.core.agents.workflow_agents.tools.ocr import (
    _extract_text_from_image,
    _extract_text_from_pdf_images,
    _get_image_text_confidence,
)


# ============================================================================
# IMAGE OCR TESTS
# ============================================================================


@pytest.mark.asyncio
@pytest.mark.requires_tesseract
async def test_extract_text_from_image(sample_image_with_text: Path) -> None:
    """Test extracting text from image."""
    result = await _extract_text_from_image(str(sample_image_with_text))

    assert result["success"] is True
    assert "text" in result
    # Sample image contains "Hello World"
    assert len(result["text"]) > 0


@pytest.mark.asyncio
@pytest.mark.requires_tesseract
async def test_extract_text_from_image_missing_file() -> None:
    """Test extracting text from non-existent image."""
    result = await _extract_text_from_image("/nonexistent/image.png")

    assert result["success"] is False
    assert "error" in result


@pytest.mark.asyncio
@pytest.mark.requires_tesseract
async def test_extract_text_from_image_language(sample_image_with_text: Path) -> None:
    """Test extracting text with language parameter."""
    result = await _extract_text_from_image(str(sample_image_with_text), language="eng")

    assert result["success"] is True


# ============================================================================
# PDF OCR TESTS
# ============================================================================


@pytest.mark.asyncio
@pytest.mark.requires_tesseract
async def test_extract_text_from_pdf_images(sample_pdf: Path) -> None:
    """Test extracting text from scanned PDF."""
    result = await _extract_text_from_pdf_images(str(sample_pdf))

    assert result["success"] is True
    assert "pages" in result
    assert result["total_pages"] > 0


@pytest.mark.asyncio
@pytest.mark.requires_tesseract
async def test_extract_text_from_pdf_images_missing_file() -> None:
    """Test extracting text from non-existent PDF."""
    result = await _extract_text_from_pdf_images("/nonexistent/file.pdf")

    assert result["success"] is False
    assert "error" in result


# ============================================================================
# CONFIDENCE TESTS
# ============================================================================


@pytest.mark.asyncio
@pytest.mark.requires_tesseract
async def test_get_image_text_confidence(sample_image_with_text: Path) -> None:
    """Test getting text with confidence scores."""
    result = await _get_image_text_confidence(str(sample_image_with_text))

    assert result["success"] is True
    assert "words" in result
    assert "average_confidence" in result


@pytest.mark.asyncio
@pytest.mark.requires_tesseract
async def test_get_image_text_confidence_missing_file() -> None:
    """Test getting confidence from non-existent image."""
    result = await _get_image_text_confidence("/nonexistent/image.png")

    assert result["success"] is False
    assert "error" in result

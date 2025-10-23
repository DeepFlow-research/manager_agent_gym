"""Comprehensive tests for document processing tools.

Tests PDF, DOCX, Markdown, and format conversion operations.
"""

from pathlib import Path

import pytest

from manager_agent_gym.core.agents.workflow_agents.tools.documents import (
    _add_table_to_docx,
    _convert_docx_to_pdf,
    _convert_markdown_to_docx,
    _convert_text_to_docx,
    _create_docx,
    _create_pdf,
    _extract_docx_structure,
    _extract_pdf_tables,
    _merge_pdfs,
    _read_docx,
    _read_pdf,
    _save_markdown,
)


# ============================================================================
# PDF TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_read_pdf_success(sample_pdf: Path) -> None:
    """Test reading PDF file successfully."""
    result = await _read_pdf(str(sample_pdf))

    assert result["success"] is True
    assert "text" in result
    assert "Test Document" in result["text"]
    assert "Page 1" in result["text"]


@pytest.mark.asyncio
async def test_read_pdf_missing_file() -> None:
    """Test reading non-existent PDF."""
    result = await _read_pdf("/nonexistent/file.pdf")

    assert result["success"] is False
    assert "error" in result


@pytest.mark.asyncio
async def test_extract_pdf_tables(sample_pdf: Path) -> None:
    """Test extracting tables from PDF."""
    result = await _extract_pdf_tables(str(sample_pdf))

    assert result["success"] is True
    assert "tables" in result
    # Sample PDF has one table with headers
    assert len(result["tables"]) > 0


@pytest.mark.asyncio
async def test_extract_pdf_tables_specific_page(sample_pdf: Path) -> None:
    """Test extracting tables from specific page."""
    result = await _extract_pdf_tables(str(sample_pdf), page_number=1)

    assert result["success"] is True


@pytest.mark.asyncio
async def test_merge_pdfs(sample_pdf: Path, tmp_path: Path) -> None:
    """Test merging multiple PDFs."""
    pdf1 = sample_pdf
    pdf2 = tmp_path / "pdf2.pdf"

    # Create second PDF
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer

    doc = SimpleDocTemplate(str(pdf2), pagesize=letter)
    styles = getSampleStyleSheet()
    story = [
        Paragraph("Second PDF Document", styles["Title"]),
        Spacer(1, 0.2),
        Paragraph("This is the second PDF.", styles["BodyText"]),
    ]
    doc.build(story)

    output_path = tmp_path / "merged.pdf"
    result = await _merge_pdfs([str(pdf1), str(pdf2)], str(output_path))

    assert result["success"] is True
    assert result["merged_count"] == 2
    assert output_path.exists()


@pytest.mark.asyncio
async def test_create_pdf(tmp_path: Path) -> None:
    """Test creating PDF from text."""
    try:
        import reportlab
    except ImportError:
        pytest.skip("reportlab not installed")

    output_path = tmp_path / "created.pdf"
    content = "Hello World\n\nThis is test content."

    result = await _create_pdf(content, str(output_path), title="Test PDF")

    assert result["success"] is True
    assert output_path.exists()
    assert result["file_size"] > 0


# ============================================================================
# DOCX TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_read_docx_success(sample_docx: Path) -> None:
    """Test reading DOCX file successfully."""
    result = await _read_docx(str(sample_docx))

    assert result["success"] is True
    assert "text" in result
    assert "Test Document" in result["text"]


@pytest.mark.asyncio
async def test_read_docx_missing_file() -> None:
    """Test reading non-existent DOCX."""
    result = await _read_docx("/nonexistent/file.docx")

    assert result["success"] is False
    assert "error" in result


@pytest.mark.asyncio
async def test_create_docx(tmp_path: Path) -> None:
    """Test creating DOCX file."""
    output_path = tmp_path / "created.docx"
    content = "# Main Title\n\nThis is content.\n\n## Section 1\n\nMore content."

    result = await _create_docx(content, str(output_path), title="Test Doc")

    assert result["success"] is True
    assert output_path.exists()


@pytest.mark.asyncio
async def test_create_docx_formal_template(tmp_path: Path) -> None:
    """Test creating DOCX with formal template."""
    output_path = tmp_path / "formal.docx"
    content = "Formal content here."

    result = await _create_docx(
        content, str(output_path), title="Formal Document", template_style="formal"
    )

    assert result["success"] is True
    assert output_path.exists()


@pytest.mark.asyncio
async def test_add_table_to_docx(sample_docx: Path, tmp_path: Path) -> None:
    """Test adding table to existing DOCX."""
    output_docx = tmp_path / "with_table.docx"

    # Copy sample docx to output location
    import shutil

    shutil.copy(str(sample_docx), str(output_docx))

    table_data = [
        ["Product", "Quantity", "Price"],
        ["Apple", "10", "$5"],
        ["Banana", "20", "$10"],
    ]

    result = await _add_table_to_docx(str(output_docx), table_data, header_row=True)

    assert result["success"] is True


@pytest.mark.asyncio
async def test_extract_docx_structure(sample_docx: Path) -> None:
    """Test extracting structure from DOCX."""
    result = await _extract_docx_structure(str(sample_docx))

    assert result["success"] is True
    assert "structure" in result
    assert len(result["structure"]) > 0


# ============================================================================
# CONVERTER TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_convert_markdown_to_docx(tmp_path: Path) -> None:
    """Test converting Markdown to DOCX."""
    output_path = tmp_path / "from_markdown.docx"
    markdown_content = """# Main Title

This is content.

## Section 1

- Item 1
- Item 2

## Section 2

More content.
"""

    result = await _convert_markdown_to_docx(markdown_content, str(output_path))

    assert result["success"] is True
    assert output_path.exists()


@pytest.mark.asyncio
async def test_convert_text_to_docx(tmp_path: Path) -> None:
    """Test converting plain text to DOCX."""
    output_path = tmp_path / "from_text.docx"
    text_content = "This is plain text.\n\nWith multiple paragraphs."

    result = await _convert_text_to_docx(text_content, str(output_path), font_size=12)

    assert result["success"] is True
    assert output_path.exists()


@pytest.mark.asyncio
@pytest.mark.requires_libreoffice
async def test_convert_docx_to_pdf(sample_docx: Path, tmp_path: Path) -> None:
    """Test converting DOCX to PDF (requires LibreOffice)."""
    output_path = tmp_path / "from_docx.pdf"

    result = await _convert_docx_to_pdf(str(sample_docx), str(output_path))

    assert result["success"] is True
    assert output_path.exists()


@pytest.mark.asyncio
async def test_convert_docx_to_pdf_with_markdown_file(tmp_path: Path) -> None:
    """Test that convert_docx_to_pdf rejects markdown files."""
    # Create a markdown file
    md_path = tmp_path / "test.md"
    md_path.write_text("# Test Markdown\n\nSome content.")

    output_path = tmp_path / "output.pdf"

    result = await _convert_docx_to_pdf(str(md_path), str(output_path))

    assert result["success"] is False
    assert "Invalid file type" in result["error"]
    assert ".md" in result["error"]
    assert "convert_markdown_to_docx" in result["error"]


@pytest.mark.asyncio
async def test_convert_docx_to_pdf_with_txt_file(tmp_path: Path) -> None:
    """Test that convert_docx_to_pdf rejects plain text files."""
    # Create a text file
    txt_path = tmp_path / "test.txt"
    txt_path.write_text("Some plain text content.")

    output_path = tmp_path / "output.pdf"

    result = await _convert_docx_to_pdf(str(txt_path), str(output_path))

    assert result["success"] is False
    assert "Invalid file type" in result["error"]
    assert ".txt" in result["error"]


@pytest.mark.asyncio
async def test_convert_docx_to_pdf_with_pdf_file(tmp_path: Path) -> None:
    """Test that convert_docx_to_pdf rejects PDF files."""
    # Create a dummy PDF file
    pdf_path = tmp_path / "test.pdf"
    pdf_path.write_text("%PDF-1.4\n")  # Minimal PDF header

    output_path = tmp_path / "output.pdf"

    result = await _convert_docx_to_pdf(str(pdf_path), str(output_path))

    assert result["success"] is False
    assert "Invalid file type" in result["error"]
    assert ".pdf" in result["error"]


# ============================================================================
# MARKDOWN TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_save_markdown(tmp_path: Path) -> None:
    """Test saving markdown file."""
    content = """# Title

This is content.

## Section

More content.
"""

    result = await _save_markdown(content, "test_doc")

    assert result["success"] is True
    assert "file_path" in result
    assert result["file_name"] == "test_doc.md"
    assert "content_summary" in result
    assert result["content_summary"]["word_count"] > 0


@pytest.mark.asyncio
async def test_save_markdown_with_extension(tmp_path: Path) -> None:
    """Test saving markdown file with extension."""
    content = "# Content\n\nBody text."

    result = await _save_markdown(content, "test_doc.md")

    assert result["success"] is True
    assert result["file_name"] == "test_doc.md"


# ============================================================================
# ERROR HANDLING TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_merge_pdfs_no_files() -> None:
    """Test merging with no files."""
    result = await _merge_pdfs([], "/tmp/output.pdf")

    assert result["success"] is False
    assert "error" in result


@pytest.mark.asyncio
async def test_add_table_to_docx_missing_file(tmp_path: Path) -> None:
    """Test adding table to non-existent DOCX."""
    result = await _add_table_to_docx("/nonexistent.docx", [["a", "b"]])

    assert result["success"] is False
    assert "error" in result


@pytest.mark.asyncio
async def test_add_table_to_docx_empty_data(sample_docx: Path) -> None:
    """Test adding empty table."""
    result = await _add_table_to_docx(str(sample_docx), [])

    assert result["success"] is False
    assert "error" in result

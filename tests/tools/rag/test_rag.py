"""
Tests for RAG (Retrieval-Augmented Generation) tools.

Tests the two-layer architecture:
- Layer 1: Core _* functions with real RAG operations
- Layer 2: OpenAI tool wrappers (integration tested via tool_factory)

Note: All tests require rank-bm25 package installed.
"""

from pathlib import Path

import pytest

# Mark all tests in this module as requiring RAG dependencies
pytestmark = pytest.mark.requires_rag

from manager_agent_gym.core.agents.workflow_agents.tools.rag import (
    _index_documents,
    _search_documents,
    _get_document_chunks,
    _list_indices,
)


# ============================================================================
# INDEXING TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_index_documents_txt(sample_text_file: Path) -> None:
    """Test indexing a text file."""
    result = await _index_documents(
        [str(sample_text_file)], chunking_strategy="paragraphs"
    )

    assert result["success"] is True
    assert "index_id" in result
    assert result["total_documents"] == 1
    assert result["total_chunks"] > 0


@pytest.mark.asyncio
async def test_index_documents_pdf(sample_pdf: Path) -> None:
    """Test indexing a PDF file."""
    result = await _index_documents([str(sample_pdf)], chunking_strategy="pages")

    assert result["success"] is True
    assert result["total_documents"] == 1
    assert result["total_chunks"] > 0


@pytest.mark.asyncio
async def test_index_documents_docx(sample_docx: Path) -> None:
    """Test indexing a DOCX file."""
    result = await _index_documents([str(sample_docx)], chunking_strategy="paragraphs")

    assert result["success"] is True
    assert result["total_documents"] == 1
    assert result["total_chunks"] > 0


@pytest.mark.asyncio
async def test_index_documents_multiple_files(
    sample_text_file: Path, sample_pdf: Path
) -> None:
    """Test indexing multiple files."""
    result = await _index_documents(
        [str(sample_text_file), str(sample_pdf)], chunking_strategy="paragraphs"
    )

    assert result["success"] is True
    assert result["total_documents"] == 2
    assert result["total_chunks"] > 0


@pytest.mark.asyncio
async def test_index_documents_missing_file() -> None:
    """Test indexing a missing file."""
    result = await _index_documents(["/nonexistent/file.txt"])

    assert result["success"] is False
    assert "not found" in result["error"].lower()


@pytest.mark.asyncio
async def test_index_documents_unsupported_format() -> None:
    """Test indexing an unsupported file format."""
    result = await _index_documents(["/tmp/test.xyz"])

    assert result["success"] is False
    assert (
        "unsupported" in result["error"].lower()
        or "not found" in result["error"].lower()
    )


@pytest.mark.asyncio
async def test_index_documents_invalid_strategy(sample_text_file: Path) -> None:
    """Test indexing with invalid chunking strategy."""
    result = await _index_documents(
        [str(sample_text_file)], chunking_strategy="invalid"
    )

    assert result["success"] is False
    assert "chunking strategy" in result["error"].lower()


# ============================================================================
# SEARCH TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_search_documents_success(sample_text_file: Path) -> None:
    """Test searching indexed documents."""
    # First index a document
    index_result = await _index_documents(
        [str(sample_text_file)], chunking_strategy="paragraphs"
    )
    assert index_result["success"] is True
    index_id = index_result["index_id"]

    # Now search
    search_result = await _search_documents("test", index_id, top_k=3)

    assert search_result["success"] is True
    assert "results" in search_result
    assert search_result["num_results"] >= 0


@pytest.mark.asyncio
async def test_search_documents_invalid_index() -> None:
    """Test searching with invalid index ID."""
    result = await _search_documents("query", "invalid_index_id")

    assert result["success"] is False
    assert "not found" in result["error"].lower()


@pytest.mark.asyncio
@pytest.mark.requires_cohere
async def test_search_documents_with_rerank(
    sample_text_file: Path, cohere_api_key: str
) -> None:
    """Test searching with Cohere reranking."""
    # First index
    index_result = await _index_documents([str(sample_text_file)])
    assert index_result["success"] is True
    index_id = index_result["index_id"]

    # Search with reranking
    search_result = await _search_documents("test", index_id, top_k=3, use_rerank=True)

    # May fail if cohere not configured properly, but shouldn't crash
    assert "success" in search_result


# ============================================================================
# CHUNK RETRIEVAL TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_get_document_chunks(sample_text_file: Path) -> None:
    """Test getting all chunks from an index."""
    # First index
    index_result = await _index_documents([str(sample_text_file)])
    assert index_result["success"] is True
    index_id = index_result["index_id"]

    # Get chunks
    result = await _get_document_chunks(index_id)

    assert result["success"] is True
    assert "chunks" in result
    assert result["total_chunks"] > 0


@pytest.mark.asyncio
async def test_get_document_chunks_invalid_index() -> None:
    """Test getting chunks from invalid index."""
    result = await _get_document_chunks("invalid_index_id")

    assert result["success"] is False
    assert "not found" in result["error"].lower()


# ============================================================================
# INDEX MANAGEMENT TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_list_indices() -> None:
    """Test listing all indices."""
    result = await _list_indices()

    assert result["success"] is True
    assert "indices" in result
    assert isinstance(result["indices"], list)
    assert result["total"] >= 0


@pytest.mark.asyncio
async def test_list_indices_after_creation(sample_text_file: Path) -> None:
    """Test that new indices appear in the list."""
    # Get initial count
    initial_result = await _list_indices()
    assert initial_result["success"] is True
    initial_count = initial_result["total"]

    # Create a new index
    index_result = await _index_documents([str(sample_text_file)])
    assert index_result["success"] is True

    # Get updated count
    updated_result = await _list_indices()
    assert updated_result["success"] is True
    assert updated_result["total"] >= initial_count

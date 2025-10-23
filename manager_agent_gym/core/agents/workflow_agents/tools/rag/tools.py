"""RAG (Retrieval-Augmented Generation) tools - two-layer architecture.

Layer 1: Core functions (_*) - pure business logic, testable, returns typed results
Layer 2: OpenAI tool wrappers - thin adapters for OpenAI SDK, handle JSON serialization
"""

import json
from pathlib import Path
from typing import TYPE_CHECKING, Any

import cohere
import pdfplumber
from agents import Tool, function_tool
from docx import Document

from .chunking import DocumentChunker
from .indexing import get_index_manager

if TYPE_CHECKING:
    from manager_agent_gym.core.workflow.resource_storage import ResourceFileManager


# ============================================================================
# LAYER 1: RAG OPERATIONS (Core Business Logic)
# ============================================================================


async def _index_documents(
    file_paths: list[str], chunking_strategy: str = "paragraphs"
) -> dict[str, Any]:
    """Index documents for RAG retrieval."""
    try:
        manager = get_index_manager()
        index_id = manager.create_index()
        index = manager.get_index(index_id)

        if index is None:
            return {"success": False, "error": "Failed to create index"}

        total_chunks = 0
        processed_files = []

        for file_path in file_paths:
            file_path_obj = Path(file_path)
            if not file_path_obj.exists():
                return {"success": False, "error": f"File not found: {file_path}"}

            # Read file based on extension
            file_ext = file_path_obj.suffix.lower()

            if file_ext == ".txt":
                text = file_path_obj.read_text(encoding="utf-8", errors="ignore")
            elif file_ext == ".pdf":
                with pdfplumber.open(file_path) as pdf:
                    pages_text = []
                    for page_num, page in enumerate(pdf.pages, start=1):
                        page_text = page.extract_text()
                        if page_text:
                            pages_text.append(f"--- Page {page_num} ---\n{page_text}")
                    text = "\n\n".join(pages_text)
            elif file_ext in [".docx", ".doc"]:
                doc = Document(file_path)
                paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
                text = "\n\n".join(paragraphs)
            else:
                return {"success": False, "error": f"Unsupported file type: {file_ext}"}

            # Chunk the document
            chunker = DocumentChunker()

            if chunking_strategy == "paragraphs":
                chunks = chunker.chunk_by_paragraphs(
                    text, max_chunk_size=1000, overlap=100
                )
            elif chunking_strategy == "pages":
                chunks = chunker.chunk_by_pages(text)
            elif chunking_strategy == "sentences":
                chunks = chunker.chunk_by_sentences(text, sentences_per_chunk=5)
            else:
                return {
                    "success": False,
                    "error": f"Unknown chunking strategy: {chunking_strategy}",
                }

            # Add chunks to index
            index.add_documents(chunks, doc_source=str(file_path_obj))
            total_chunks += len(chunks)
            processed_files.append({"file": str(file_path_obj), "chunks": len(chunks)})

        # Build the BM25 index
        index.build_index()

        return {
            "success": True,
            "index_id": index_id,
            "total_documents": len(file_paths),
            "total_chunks": total_chunks,
            "files_processed": processed_files,
        }

    except Exception as e:
        return {"success": False, "error": f"Error indexing documents: {str(e)}"}


async def _search_documents(
    query: str, index_id: str, top_k: int = 5, use_rerank: bool = False
) -> dict[str, Any]:
    """Search indexed documents."""
    try:
        manager = get_index_manager()
        index = manager.get_index(index_id)

        if index is None:
            return {"success": False, "error": f"Index not found: {index_id}"}

        # Perform BM25 search
        results = index.search(query, top_k=top_k * 2 if use_rerank else top_k)

        if use_rerank:
            try:
                co = cohere.Client()
                docs = [r["text"] for r in results]
                rerank_response = co.rerank(
                    query=query,
                    documents=docs,
                    top_n=top_k,
                    model="rerank-english-v2.0",
                )
                # Reorder results based on reranking
                reranked_results = [results[r.index] for r in rerank_response.results]
                results = reranked_results
            except Exception as e:
                return {"success": False, "error": f"Reranking error: {str(e)}"}
        else:
            results = results[:top_k]

        return {"success": True, "results": results, "num_results": len(results)}

    except Exception as e:
        return {"success": False, "error": f"Search error: {str(e)}"}


async def _get_document_chunks(index_id: str) -> dict[str, Any]:
    """Get all chunks from an index."""
    try:
        manager = get_index_manager()
        index = manager.get_index(index_id)

        if index is None:
            return {"success": False, "error": f"Index not found: {index_id}"}

        chunks = index.get_all_documents()
        return {"success": True, "chunks": chunks, "total_chunks": len(chunks)}

    except Exception as e:
        return {"success": False, "error": f"Error getting chunks: {str(e)}"}


async def _list_indices() -> dict[str, Any]:
    """List all available indices."""
    try:
        manager = get_index_manager()
        indices = manager.list_indices()
        return {"success": True, "indices": indices, "total": len(indices)}

    except Exception as e:
        return {"success": False, "error": f"Error listing indices: {str(e)}"}


# ============================================================================
# LAYER 2: OPENAI TOOL WRAPPERS
# ============================================================================


def create_rag_tools(resource_manager: "ResourceFileManager") -> list[Tool]:
    """Create RAG tools for OpenAI SDK."""

    @function_tool
    async def index_reference_documents(
        file_paths: list[str], chunking_strategy: str = "paragraphs"
    ) -> str:
        """
        Index documents for intelligent semantic search and retrieval (RAG).

        This tool processes documents (PDF, DOCX, TXT) and creates a searchable index
        using BM25 ranking. Documents are split into chunks based on your chosen strategy,
        allowing efficient retrieval of relevant information later. Perfect for creating
        knowledge bases from documentation, policies, or reference materials.

        Parameters:
            file_paths (list[str]):
                List of paths to documents to index. Supported formats: PDF, DOCX, TXT.
                Example: ["/path/to/manual.pdf", "/path/to/policy.docx"]
            chunking_strategy (str):
                How to split documents into searchable chunks. Options:
                - "paragraphs": Split by paragraph boundaries (default, good for most docs)
                - "pages": Split by page breaks (good for PDFs with page-based structure)
                - "sentences": Split by sentences (good for very granular search)
                Default: "paragraphs"

        Returns:
            str:
                JSON string containing:
                - index_id: Unique identifier for the created index (save this for searches!)
                - total_documents: Number of documents processed
                - total_chunks: Total number of searchable chunks created
                - files_processed: Details for each file (name and chunk count)
                Or an error message if indexing fails.

        Usage:
            Call this tool first to create a searchable knowledge base from documents.
            Save the returned index_id to use with search_documents. Common uses include:
            indexing documentation, creating reference databases, building knowledge bases,
            or preparing documents for question-answering systems.
        """
        result = await _index_documents(file_paths, chunking_strategy)
        if result["success"]:
            return json.dumps(
                {
                    "index_id": result["index_id"],
                    "total_documents": result["total_documents"],
                    "total_chunks": result["total_chunks"],
                    "files_processed": result["files_processed"],
                },
                indent=2,
            )
        return f"Error: {result.get('error')}"

    @function_tool
    async def search_documents(
        query: str, index_id: str, top_k: int = 5, use_rerank: bool = False
    ) -> str:
        """
        Search indexed documents to find relevant information using BM25 ranking.

        This tool performs intelligent semantic search across documents you've previously
        indexed. It finds the most relevant chunks of text based on your query using
        BM25 algorithm, and optionally reranks results using advanced models for even
        better accuracy. Perfect for finding specific information in large document sets.

        Parameters:
            query (str):
                Your search question or keywords. Be specific for best results.
                Example: "What are the safety requirements?" or "budget allocation process"
            index_id (str):
                The index identifier returned from index_reference_documents.
                Example: "abc123-def456"
            top_k (int):
                Number of relevant results to return. Higher values give more context
                but may include less relevant results. Default: 5. Recommended: 3-10.
            use_rerank (bool):
                Whether to use advanced reranking for better result quality. Requires
                Cohere API. Set to True for improved accuracy on complex queries.
                Default: False.

        Returns:
            str:
                JSON string containing:
                - success: Whether the search succeeded
                - results: Array of relevant document chunks with text and metadata
                - num_results: Number of results returned
                Or an error message if the search fails.

        Usage:
            Use this tool after indexing documents to find relevant information. Common
            uses include: answering questions from documentation, finding policy details,
            retrieving specific procedures, or getting context from large document sets.
            Always save and reuse the index_id from your indexing step.
        """
        result = await _search_documents(query, index_id, top_k, use_rerank)
        if result["success"]:
            return json.dumps(result, indent=2)
        return f"Error: {result.get('error')}"

    @function_tool
    async def get_document_chunks(index_id: str) -> str:
        """
        Retrieve all document chunks from a specific index for inspection or analysis.

        This tool returns all the text chunks that were created during document indexing.
        Useful for understanding what content is in your index, debugging search results,
        or reviewing how documents were chunked. Each chunk includes its text and source
        document information.

        Parameters:
            index_id (str):
                The index identifier from index_reference_documents.
                Example: "abc123-def456"

        Returns:
            str:
                JSON string containing:
                - success: Whether the operation succeeded
                - chunks: Array of all document chunks with text and metadata
                - total_chunks: Total number of chunks in the index
                Or an error message if the index is not found.

        Usage:
            Call this tool when you need to see all indexed content, verify what was
            indexed, debug search results, or understand the structure of your document
            index. Useful for quality control and understanding index contents.
        """
        result = await _get_document_chunks(index_id)
        if result["success"]:
            return json.dumps(result, indent=2)
        return f"Error: {result.get('error')}"

    @function_tool
    async def list_document_indices() -> str:
        """
        List all available document indices in the system.

        This tool returns a list of all document indices that have been created during
        your session. Each index represents a set of indexed documents. Use this to
        discover available indices, find index IDs you've created, or manage multiple
        document collections.

        Parameters:
            None required.

        Returns:
            str:
                JSON string containing:
                - success: Whether the operation succeeded
                - indices: Array of index information (index IDs and metadata)
                - total: Total number of indices available
                Or an error message if listing fails.

        Usage:
            Call this tool when you need to see what document indices exist, find an
            index ID you created earlier, or check what document collections are available
            for searching. Useful for managing multiple document sets or recovering
            index IDs from previous indexing operations.
        """
        result = await _list_indices()
        if result["success"]:
            return json.dumps(result, indent=2)
        return f"Error: {result.get('error')}"

    return [
        index_reference_documents,
        search_documents,
        get_document_chunks,
        list_document_indices,
    ]

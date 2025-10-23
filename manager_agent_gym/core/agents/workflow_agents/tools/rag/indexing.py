"""BM25-based search implementation for document retrieval."""

from typing import Any
from uuid import uuid4


class DocumentIndex:
    """In-memory document index using BM25."""

    def __init__(self, index_id: str | None = None):
        """
        Initialize a new document index.

        Args:
            index_id: Optional unique identifier for this index
        """
        self.index_id = index_id or str(uuid4())
        self.documents: list[dict[str, Any]] = []
        self.bm25: Any = None
        self._corpus: list[list[str]] = []

    def add_documents(
        self, documents: list[dict[str, Any]], doc_source: str | None = None
    ) -> None:
        """
        Add documents to the index.

        Args:
            documents: List of document dictionaries with 'text' field
            doc_source: Optional source identifier (e.g., file path)
        """
        for doc in documents:
            doc_copy = doc.copy()
            doc_copy["doc_id"] = len(self.documents)
            doc_copy["source"] = doc_source
            self.documents.append(doc_copy)

    def build_index(self) -> None:
        """Build the BM25 index from added documents."""
        try:
            from rank_bm25 import BM25Okapi
        except ImportError:
            raise ImportError(
                "rank-bm25 not installed. Install with: pip install rank-bm25"
            )

        # Tokenize documents
        self._corpus = [self._tokenize(doc["text"]) for doc in self.documents]

        # Build BM25 index
        self.bm25 = BM25Okapi(self._corpus)

    def search(
        self, query: str, top_k: int = 5, min_score: float = 0.0
    ) -> list[dict[str, Any]]:
        """
        Search the index for relevant documents.

        Args:
            query: Search query
            top_k: Number of top results to return
            min_score: Minimum BM25 score threshold

        Returns:
            List of result dictionaries with documents and scores
        """
        if self.bm25 is None:
            raise ValueError("Index not built. Call build_index() first.")

        # Tokenize query
        query_tokens = self._tokenize(query)

        # Get BM25 scores
        scores = self.bm25.get_scores(query_tokens)

        # Get top-k results
        top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[
            :top_k
        ]

        results = []
        for idx in top_indices:
            score = scores[idx]
            if score >= min_score:
                result = self.documents[idx].copy()
                result["score"] = float(score)
                results.append(result)

        return results

    def get_document(self, doc_id: int) -> dict[str, Any] | None:
        """
        Get a document by its ID.

        Args:
            doc_id: Document ID

        Returns:
            Document dictionary or None if not found
        """
        if 0 <= doc_id < len(self.documents):
            return self.documents[doc_id]
        return None

    def get_all_documents(self) -> list[dict[str, Any]]:
        """
        Get all documents in the index.

        Returns:
            List of all document dictionaries
        """
        return self.documents

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        """
        Simple tokenization (split by whitespace and lowercase).

        Args:
            text: Text to tokenize

        Returns:
            List of tokens
        """
        return text.lower().split()

    def to_dict(self) -> dict[str, Any]:
        """Serialize index to dictionary."""
        return {
            "index_id": self.index_id,
            "documents": self.documents,
            "num_documents": len(self.documents),
        }


class DocumentIndexManager:
    """Manages multiple document indices in memory."""

    def __init__(self):
        self._indices: dict[str, DocumentIndex] = {}

    def create_index(self, index_id: str | None = None) -> str:
        """
        Create a new document index.

        Args:
            index_id: Optional index identifier

        Returns:
            Index ID
        """
        index = DocumentIndex(index_id)
        self._indices[index.index_id] = index
        return index.index_id

    def get_index(self, index_id: str) -> DocumentIndex | None:
        """Get an index by ID."""
        return self._indices.get(index_id)

    def delete_index(self, index_id: str) -> bool:
        """Delete an index by ID."""
        if index_id in self._indices:
            del self._indices[index_id]
            return True
        return False

    def list_indices(self) -> list[str]:
        """List all index IDs."""
        return list(self._indices.keys())


# Global index manager instance
_INDEX_MANAGER = DocumentIndexManager()


def get_index_manager() -> DocumentIndexManager:
    """Get the global index manager instance."""
    return _INDEX_MANAGER

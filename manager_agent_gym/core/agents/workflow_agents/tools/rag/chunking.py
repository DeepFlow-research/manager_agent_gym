"""Document chunking strategies for RAG."""


class DocumentChunker:
    """Handles chunking of documents for RAG indexing."""

    @staticmethod
    def chunk_by_paragraphs(
        text: str, max_chunk_size: int = 1000, overlap: int = 100
    ) -> list[dict]:
        """
        Chunk text by paragraphs with size limit and overlap.

        Args:
            text: Input text to chunk
            max_chunk_size: Maximum characters per chunk
            overlap: Number of characters to overlap between chunks

        Returns:
            List of chunk dictionaries with text and metadata
        """
        paragraphs = text.split("\n\n")
        chunks = []
        current_chunk = ""
        chunk_idx = 0

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            # If adding this paragraph would exceed max size, finalize current chunk
            if current_chunk and len(current_chunk) + len(para) + 2 > max_chunk_size:
                chunks.append(
                    {
                        "chunk_id": chunk_idx,
                        "text": current_chunk.strip(),
                        "char_start": sum(len(c["text"]) for c in chunks),
                    }
                )
                chunk_idx += 1

                # Start new chunk with overlap
                if overlap > 0:
                    words = current_chunk.split()
                    overlap_text = " ".join(words[-overlap:])
                    current_chunk = overlap_text + "\n\n" + para
                else:
                    current_chunk = para
            else:
                if current_chunk:
                    current_chunk += "\n\n" + para
                else:
                    current_chunk = para

        # Add final chunk
        if current_chunk:
            chunks.append(
                {
                    "chunk_id": chunk_idx,
                    "text": current_chunk.strip(),
                    "char_start": sum(len(c["text"]) for c in chunks),
                }
            )

        return chunks

    @staticmethod
    def chunk_by_sentences(
        text: str, sentences_per_chunk: int = 5, overlap_sentences: int = 1
    ) -> list[dict]:
        """
        Chunk text by sentences.

        Args:
            text: Input text to chunk
            sentences_per_chunk: Number of sentences per chunk
            overlap_sentences: Number of sentences to overlap

        Returns:
            List of chunk dictionaries
        """
        # Simple sentence splitting (could use nltk or spacy for better results)
        import re

        sentences = re.split(r"(?<=[.!?])\s+", text)
        chunks = []
        chunk_idx = 0

        i = 0
        while i < len(sentences):
            chunk_sentences = sentences[i : i + sentences_per_chunk]
            chunk_text = " ".join(chunk_sentences)

            chunks.append(
                {
                    "chunk_id": chunk_idx,
                    "text": chunk_text.strip(),
                    "sentence_start": i,
                }
            )
            chunk_idx += 1

            # Move forward with overlap
            i += sentences_per_chunk - overlap_sentences

        return chunks

    @staticmethod
    def chunk_by_pages(text: str, page_marker: str = "--- Page") -> list[dict]:
        """
        Chunk text by page markers (useful for PDFs).

        Args:
            text: Input text with page markers
            page_marker: String that indicates page boundaries

        Returns:
            List of chunk dictionaries with page numbers
        """
        chunks = []
        pages = text.split(page_marker)

        for idx, page_text in enumerate(pages):
            page_text = page_text.strip()
            if not page_text:
                continue

            # Extract page number if present
            page_num = None
            if page_text.split("\n")[0].strip().replace("---", "").strip().isdigit():
                first_line = page_text.split("\n")[0]
                page_num = int(first_line.strip().replace("---", "").strip())
                page_text = "\n".join(page_text.split("\n")[1:]).strip()

            chunks.append(
                {
                    "chunk_id": idx,
                    "text": page_text,
                    "page_number": page_num or idx,
                }
            )

        return chunks

    @staticmethod
    def chunk_with_headers(
        text: str, header_pattern: str = r"^#{1,3}\s+"
    ) -> list[dict]:
        """
        Chunk text preserving markdown headers as context.

        Args:
            text: Input markdown text
            header_pattern: Regex pattern for headers

        Returns:
            List of chunk dictionaries with header context
        """
        import re

        lines = text.split("\n")
        chunks = []
        current_chunk = []
        current_headers = []
        chunk_idx = 0

        for line in lines:
            if re.match(header_pattern, line):
                # New section detected
                if current_chunk:
                    chunks.append(
                        {
                            "chunk_id": chunk_idx,
                            "text": "\n".join(current_chunk).strip(),
                            "headers": list(current_headers),
                        }
                    )
                    chunk_idx += 1
                    current_chunk = []

                # Update header context
                level = len(line) - len(line.lstrip("#"))
                current_headers = current_headers[:level] + [line.strip("# ")]

            current_chunk.append(line)

        # Add final chunk
        if current_chunk:
            chunks.append(
                {
                    "chunk_id": chunk_idx,
                    "text": "\n".join(current_chunk).strip(),
                    "headers": list(current_headers),
                }
            )

        return chunks

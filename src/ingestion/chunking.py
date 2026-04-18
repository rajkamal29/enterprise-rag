"""Chunking strategy with metadata contract for shared retrieval."""

import hashlib
import logging
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)


@dataclass
class Chunk:
    """Represents a single document chunk with metadata.
    
    This is the shared contract between Track A (AI Foundry) and Track B (Custom Agent).
    """

    chunk_id: str  # Unique identifier: f"{doc_hash}_{chunk_index}"
    source_document: str  # Original file path or URL
    chunk_text: str  # The actual text content
    chunk_index: int  # Position within document (0-based)
    document_title: str  # Human-readable document name
    document_hash: str  # Hash of entire document (for deduplication)
    page_number: Optional[int] = None  # If available
    section_title: Optional[str] = None  # If structure extracted
    character_count: int = 0
    token_estimate: int = 0  # Rough estimate for LLM token budgeting

    def to_dict(self) -> dict[str, Any]:
        """Convert chunk to dictionary for indexing."""
        return asdict(self)


class ChunkingStrategy:
    """Implements fixed-size chunking with overlap for semantic coherence."""

    def __init__(
        self,
        chunk_size: int = 1024,
        chunk_overlap: int = 128,
        separator: str = "\n\n",
    ):
        """Initialize chunking strategy.
        
        Args:
            chunk_size: Target characters per chunk
            chunk_overlap: Overlap characters between chunks for context
            separator: Paragraph separator to respect
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separator = separator

    def chunk_document(self, document: dict[str, Any]) -> list["Chunk"]:
        """Split document into chunks with metadata.
        
        Args:
            document: Output from DocumentParser.parse_document()
            
        Returns:
            List of Chunk objects
        """
        source = document.get("source", "unknown")
        title = document.get("title", Path(source).stem if isinstance(source, str) else "unknown")
        content = document.get("content", "")
        pages = document.get("pages", 1)
        
        if not content.strip():
            logger.warning(f"Document {source} has no content to chunk")
            return []
        
        # Create document hash for deduplication
        doc_hash = hashlib.sha256(content.encode()).hexdigest()[:12]
        
        chunks = self._split_content(content, doc_hash, source, title, pages)
        logger.info(f"Chunked {source} into {len(chunks)} chunks")
        
        return chunks

    def _split_content(
        self,
        content: str,
        doc_hash: str,
        source: str,
        title: str,
        pages: int,
    ) -> list[Chunk]:
        """Split content respecting paragraph boundaries with overlap."""
        chunks = []
        
        # Split by paragraph separator first
        paragraphs = content.split(self.separator)
        
        current_chunk = ""
        chunk_index = 0
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            
            # If adding paragraph would exceed chunk_size, save current chunk
            test_chunk = f"{current_chunk}\n\n{para}".strip()
            if len(test_chunk) > self.chunk_size and current_chunk:
                # Save current chunk
                chunk_text = current_chunk.strip()
                if chunk_text:
                    chunks.append(
                        self._create_chunk(
                            chunk_text, chunk_index, doc_hash, source, title, pages
                        )
                    )
                    chunk_index += 1
                
                # Start new chunk with overlap
                overlap_text = self._extract_overlap(current_chunk)
                current_chunk = f"{overlap_text}\n\n{para}".strip()
            else:
                current_chunk = test_chunk
        
        # Save final chunk
        if current_chunk.strip():
            chunks.append(
                self._create_chunk(
                    current_chunk.strip(), chunk_index, doc_hash, source, title, pages
                )
            )
        
        return chunks

    def _extract_overlap(self, text: str) -> str:
        """Extract last N characters for overlap to next chunk."""
        if len(text) <= self.chunk_overlap:
            return text
        
        # Try to break at sentence boundary within overlap window
        search_start = len(text) - self.chunk_overlap
        remaining = text[search_start:]
        
        # Find last period, question mark, or exclamation
        for sep in [".", "?", "!"]:
            idx = remaining.rfind(sep)
            if idx > 0:
                return text[search_start + idx + 1 :].strip()
        
        return remaining.strip()

    def _create_chunk(
        self,
        text: str,
        chunk_index: int,
        doc_hash: str,
        source: str,
        title: str,
        total_pages: int,
    ) -> Chunk:
        """Create a Chunk object with calculated metadata."""
        chunk_id = f"{doc_hash}_{chunk_index:04d}"
        char_count = len(text)
        # Rough token estimate: ~4 chars per token for English
        token_estimate = int(char_count / 4) + 50  # Buffer for metadata
        
        # Estimate page (rough approximation)
        page_num = None
        if total_pages > 1 and chunk_index > 0:
            page_num = min(1 + (chunk_index * total_pages) // max(1, total_pages), total_pages)
        
        return Chunk(
            chunk_id=chunk_id,
            source_document=source,
            chunk_text=text,
            chunk_index=chunk_index,
            document_title=title,
            document_hash=doc_hash,
            page_number=page_num,
            section_title=None,
            character_count=char_count,
            token_estimate=token_estimate,
        )




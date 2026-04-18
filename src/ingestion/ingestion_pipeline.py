"""Idempotent document ingestion orchestration pipeline."""

import json
import logging
from pathlib import Path
from typing import Any

from .chunking import ChunkingStrategy
from .document_parser import DocumentParser
from .embeddings import EmbeddingGenerator
from .search_indexer import SearchIndexer

logger = logging.getLogger(__name__)


class IngestionPipeline:
    """Orchestrates document parsing, chunking, embedding, and indexing."""

    def __init__(
        self,
        doc_parser: DocumentParser,
        chunking_strategy: ChunkingStrategy,
        embedding_gen: EmbeddingGenerator,
        search_indexer: SearchIndexer,
        state_file: Path | None = None,
    ) -> None:
        """Initialize ingestion pipeline.
        
        Args:
            doc_parser: DocumentParser instance
            chunking_strategy: ChunkingStrategy instance
            embedding_gen: EmbeddingGenerator instance
            search_indexer: SearchIndexer instance
            state_file: Optional file to track ingested documents (for idempotence)
        """
        self.doc_parser = doc_parser
        self.chunking_strategy = chunking_strategy
        self.embedding_gen = embedding_gen
        self.search_indexer = search_indexer
        self.state_file = state_file or Path(".ingestion_state.json")
        self.ingested_documents = self._load_state()

    def ingest_documents(self, document_paths: list[str | Path]) -> dict[str, int]:
        """Ingest documents end-to-end: parse → chunk → embed → index.
        
        Args:
            document_paths: List of file paths to ingest
            
        Returns:
            Summary of ingestion results
        """
        logger.info(f"Starting ingestion of {len(document_paths)} documents")
        
        # Ensure index exists
        self.search_indexer.create_or_update_index()
        
        all_chunks: list[dict[str, Any]] = []
        all_embeddings: list[list[float]] = []
        stats: dict[str, int] = {
            "total_documents": 0,
            "skipped_documents": 0,
            "total_chunks": 0,
        }
        
        for doc_path in document_paths:
            doc_path = Path(doc_path)
            
            # Check if already ingested (idempotence)
            doc_hash = self._compute_file_hash(doc_path)
            if doc_hash in self.ingested_documents:
                logger.info(f"Skipping already-ingested document: {doc_path.name}")
                stats["skipped_documents"] += 1
                continue
            
            try:
                # Parse document
                document = self.doc_parser.parse_document(doc_path)
                logger.info(f"Parsed: {doc_path.name}")
                
                # Chunk document
                chunks = self.chunking_strategy.chunk_document(document)
                if not chunks:
                    logger.warning(f"No chunks produced for {doc_path.name}")
                    continue
                
                # Convert chunks to dicts for embedding and indexing
                chunk_dicts = [c.to_dict() for c in chunks]
                chunk_texts = [c.chunk_text for c in chunks]
                
                # Generate embeddings
                embeddings = self.embedding_gen.embed_batch(chunk_texts)
                logger.info(f"Generated embeddings for {len(chunk_texts)} chunks")
                
                # Accumulate for batch upload
                all_chunks.extend(chunk_dicts)
                all_embeddings.extend(embeddings)
                
                stats["total_documents"] += 1
                stats["total_chunks"] += len(chunks)
                
                # Track in state
                self.ingested_documents[doc_hash] = str(doc_path)
                
            except Exception as e:
                logger.error(f"Failed to ingest {doc_path.name}: {e}")
                continue
        
        # Batch upload to search
        if all_chunks:
            uploaded = self.search_indexer.upload_chunks(all_chunks, all_embeddings)
            stats["uploaded_chunks"] = uploaded
        
        # Save state for idempotence
        self._save_state()
        
        # Get final index stats
        index_stats = self.search_indexer.get_index_stats()
        stats.update(index_stats)
        
        logger.info(f"Ingestion complete: {stats}")
        return stats

    def _compute_file_hash(self, file_path: Path) -> str:
        """Compute SHA256 hash of file for deduplication."""
        import hashlib
        
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)
        
        return sha256.hexdigest()[:12]

    def _load_state(self) -> dict[str, Any]:
        """Load ingestion state from file (for idempotence)."""
        if self.state_file.exists():
            try:
                with open(self.state_file, "r") as f:
                    state: dict[str, Any] = json.load(f)
                    logger.info(f"Loaded state: {len(state)} documents previously ingested")
                    return state
            except Exception as e:
                logger.error(f"Failed to load state: {e}")
        
        return {}

    def _save_state(self) -> None:
        """Save ingestion state to file."""
        try:
            with open(self.state_file, "w") as f:
                json.dump(self.ingested_documents, f, indent=2)
            logger.debug(
                f"Saved state: {len(self.ingested_documents)} documents tracked"
            )
        except Exception as e:
            logger.error(f"Failed to save state: {e}")

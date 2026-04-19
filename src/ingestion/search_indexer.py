"""Azure AI Search index management with vector search support."""

import logging
from typing import Any

from azure.search.documents.indexes.models import (
    HnswAlgorithmConfiguration,
    SearchableField,
    SearchField,
    SearchFieldDataType,
    SearchIndex,
    SimpleField,
    VectorSearch,
    VectorSearchProfile,
)

logger = logging.getLogger(__name__)


class SearchIndexer:
    """Manage Azure AI Search index with vector search capabilities."""

    def __init__(
        self,
        search_client: Any,
        search_index_client: Any,
        index_name: str = "rag-chunks",
    ) -> None:
        """Initialize search indexer.
        
        Args:
            search_client: SearchClient instance from AzureClientFactory
            search_index_client: SearchIndexClient instance from AzureClientFactory
            index_name: Name of index (auto-created if needed)
        """
        self.search_client = search_client
        self.search_index_client = search_index_client
        self.index_name = index_name

    def create_or_update_index(self) -> None:
        """Create or update the RAG chunk index with vector search support."""
        fields = [
            SimpleField(
                name="chunk_id",
                type=SearchFieldDataType.String,
                key=True,
                sortable=True,
            ),
            SearchableField(
                name="chunk_text",
                type=SearchFieldDataType.String,
                searchable=True,
                retrievable=True,
            ),
            SimpleField(
                name="document_title",
                type=SearchFieldDataType.String,
                retrievable=True,
                filterable=True,
            ),
            SimpleField(
                name="source_document",
                type=SearchFieldDataType.String,
                retrievable=True,
                filterable=True,
            ),
            SimpleField(
                name="chunk_index",
                type=SearchFieldDataType.Int32,
                retrievable=True,
                sortable=True,
            ),
            SimpleField(
                name="document_hash",
                type=SearchFieldDataType.String,
                retrievable=True,
                filterable=True,
            ),
            SimpleField(
                name="page_number",
                type=SearchFieldDataType.Int32,
                retrievable=True,
                filterable=True,
            ),
            SimpleField(
                name="character_count",
                type=SearchFieldDataType.Int32,
                retrievable=True,
            ),
            SimpleField(
                name="token_estimate",
                type=SearchFieldDataType.Int32,
                retrievable=True,
            ),
            SearchField(
                name="embedding",
                type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
                searchable=True,
                hidden=True,
                vector_search_dimensions=3072,  # text-embedding-3-large
                vector_search_profile_name="my-vector-config",
            ),
        ]

        # Vector search configuration
        vector_search = VectorSearch(
            algorithms=[
                HnswAlgorithmConfiguration(name="my-hnsw"),
            ],
            profiles=[
                VectorSearchProfile(
                    name="my-vector-config",
                    algorithm_configuration_name="my-hnsw",
                ),
            ],
        )

        # Create index
        index = SearchIndex(
            name=self.index_name,
            fields=fields,
            vector_search=vector_search,
        )

        try:
            self.search_index_client.create_or_update_index(index)
            logger.info(f"Created/updated index: {self.index_name}")
        except Exception as e:
            logger.error(f"Failed to create/update index: {e}")
            raise

    def upload_chunks(
        self, chunks: list[dict[str, Any]], embeddings: list[list[float]]
    ) -> int:
        """Upload chunks with embeddings to search index.
        
        Args:
            chunks: List of chunk dictionaries
            embeddings: List of embedding vectors (must match chunks length)
            
        Returns:
            Number of successfully uploaded documents
        """
        if len(chunks) != len(embeddings):
            raise ValueError(
                f"Chunks ({len(chunks)}) and embeddings ({len(embeddings)}) length mismatch"
            )

        documents: list[dict[str, Any]] = []
        for chunk, embedding in zip(chunks, embeddings, strict=True):
            doc = chunk.copy()
            doc["embedding"] = embedding
            documents.append(doc)

        try:
            result = self.search_client.upload_documents(documents)
            succeeded = sum(1 for r in result if r.succeeded)
            logger.info(f"Uploaded {succeeded}/{len(documents)} documents to {self.index_name}")
            return succeeded
        except Exception as e:
            logger.error(f"Failed to upload documents: {e}")
            raise

    def get_index_stats(self) -> dict[str, int]:
        """Get document count and other index statistics.
        
        Returns:
            Dictionary with index stats
        """
        try:
            stats = self.search_client.get_search_statistics()
            return {
                "document_count": stats.document_count,
                "storage_size_bytes": stats.storage_size,
            }
        except Exception as e:
            logger.error(f"Failed to get index stats: {e}")
            return {"document_count": 0, "storage_size_bytes": 0}

    def delete_chunks_by_hash(self, document_hash: str) -> int:
        """Delete all chunks belonging to a document identified by its hash.

        Used by the pipeline when a document's content changes, to remove
        stale chunks before re-indexing the updated version.

        Args:
            document_hash: The SHA256[:12] hash stored in the document_hash field.

        Returns:
            Number of chunks successfully deleted.
        """
        try:
            results = self.search_client.search(
                search_text="*",
                filter=f"document_hash eq '{document_hash}'",
                select=["chunk_id"],
            )
            chunk_ids = [r["chunk_id"] for r in results]
            if not chunk_ids:
                logger.info(
                    "No chunks found for document_hash=%s — nothing to delete",
                    document_hash,
                )
                return 0

            delete_docs = [{"chunk_id": cid} for cid in chunk_ids]
            result = self.search_client.delete_documents(delete_docs)
            succeeded = sum(1 for r in result if r.succeeded)
            logger.info(
                "Deleted %d/%d chunks for document_hash=%s",
                succeeded,
                len(chunk_ids),
                document_hash,
            )
            return succeeded
        except Exception as e:
            logger.error(
                "Failed to delete chunks for document_hash=%s: %s", document_hash, e
            )
            raise

    def delete_index(self) -> None:
        """Delete the entire index."""
        try:
            self.search_index_client.delete_index(self.index_name)
            logger.info(f"Deleted index: {self.index_name}")
        except Exception as e:
            logger.error(f"Failed to delete index: {e}")
            raise

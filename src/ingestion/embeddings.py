"""Embedding generation using Azure OpenAI."""

import logging
from typing import Any

logger = logging.getLogger(__name__)


class EmbeddingGenerator:
    """Generate embeddings using Azure OpenAI text-embedding-3-large model."""

    def __init__(
        self,
        openai_client: Any,
        embedding_deployment: str = "text-embedding-3-large",
    ) -> None:
        """Initialize embedding generator.
        
        Args:
            openai_client: AzureOpenAI client from AzureClientFactory
            embedding_deployment: Name of embedding deployment
        """
        self.client = openai_client
        self.embedding_deployment = embedding_deployment
        self.embedding_dimension = 3072  # text-embedding-3-large dimension

    def embed_text(self, text: str) -> list[float]:
        """Generate embedding for a single text chunk.
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector (1536 dimensions)
        """
        if not text.strip():
            logger.warning("Attempted to embed empty text")
            return [0.0] * self.embedding_dimension

        try:
            response = self.client.embeddings.create(
                input=text,
                model=self.embedding_deployment,
            )
            embedding: list[float] = response.data[0].embedding
            return embedding
        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            raise

    def embed_batch(self, texts: list[str], batch_size: int = 20) -> list[list[float]]:
        """Generate embeddings for multiple texts in batches.
        
        Args:
            texts: List of texts to embed
            batch_size: Maximum texts per API call (Azure limit ~25)
            
        Returns:
            List of embedding vectors
        """
        if not texts:
            return []

        embeddings: list[list[float]] = []
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            
            try:
                response = self.client.embeddings.create(
                    input=batch,
                    model=self.embedding_deployment,
                )
                
                # Sort by index to ensure order matches input
                batch_embeddings: list[Any] = [None] * len(batch)
                for item in response.data:
                    batch_embeddings[item.index] = item.embedding
                
                embeddings.extend([e for e in batch_embeddings if e is not None])
                logger.debug(f"Embedded batch {i // batch_size + 1}: {len(batch)} texts")
            except Exception as e:
                logger.error(f"Batch embedding failed for texts [{i}:{i+batch_size}]: {e}")
                raise
        
        return embeddings

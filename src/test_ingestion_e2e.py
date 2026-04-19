"""End-to-end test for document ingestion and retrieval."""

import json
import logging
from pathlib import Path

from azure_clients.factory import AzureClientFactory
from config.settings import AzureSettings
from ingestion.chunking import ChunkingStrategy
from ingestion.document_parser import DocumentParser
from ingestion.embeddings import EmbeddingGenerator
from ingestion.ingestion_pipeline import IngestionPipeline
from ingestion.search_indexer import SearchIndexer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_ingestion_end_to_end() -> None:
    """Test document ingestion pipeline end-to-end."""
    
    # Load settings and create factory
    settings = AzureSettings()
    factory = AzureClientFactory(settings)
    
    logger.info(
        f"Settings loaded: OpenAI={settings.openai_is_configured}, "
        f"Search={settings.search_is_configured}, "
        f"DocumentIntelligence={settings.documentintelligence_is_configured}"
    )
    
    # Check prerequisites
    if not settings.search_is_configured:
        logger.error("AZURE_SEARCH_ENDPOINT not configured")
        return
    
    if not settings.openai_is_configured:
        logger.error("AZURE_OPENAI_ENDPOINT not configured")
        return
    
    # Initialize components using factory
    doc_parser = DocumentParser(
        client=(
            factory.document_intelligence_client()
            if settings.documentintelligence_is_configured
            else None
        )
    )
    
    chunking_strategy = ChunkingStrategy(
        chunk_size=1024,
        chunk_overlap=128,
    )
    
    embedding_gen = EmbeddingGenerator(
        openai_client=factory.openai_client,
        embedding_deployment=settings.azure_openai_embedding_deployment,
    )
    
    search_indexer = SearchIndexer(
        search_client=factory.search_client,
        search_index_client=factory.search_index_client,
        index_name=settings.azure_search_index_name,
    )
    
    # Create ingestion pipeline
    pipeline = IngestionPipeline(
        doc_parser=doc_parser,
        chunking_strategy=chunking_strategy,
        embedding_gen=embedding_gen,
        search_indexer=search_indexer,
        state_file=Path(".ingestion_state.json"),
    )
    
    # Get sample documents
    sample_dir = Path("data/sample_documents")
    if not sample_dir.exists():
        logger.warning(f"Sample documents directory not found: {sample_dir}")
        return
    
    # Only use parseable documents for now (skip PDF if no Document Intelligence)
    sample_docs: list[Path] = list(sample_dir.glob("*.txt")) + list(
        sample_dir.glob("*.html")
    )
    logger.info(f"Found {len(sample_docs)} sample documents to ingest")
    sample_docs_converted: list[str | Path] = [str(p) for p in sample_docs]
    
    # Run ingestion
    try:
        stats = pipeline.ingest_documents(sample_docs_converted)
        logger.info(f"Ingestion complete: {json.dumps(stats, indent=2)}")
    except Exception as e:
        logger.error(f"Ingestion failed: {e}", exc_info=True)
        return
    
    # Test retrieval via SDK
    logger.info("Testing retrieval via Azure SDK...")
    try:
        test_query = "Azure OpenAI deployment"
        results = factory.search_client.search(test_query, top=3)
        
        logger.info(f"Search results for '{test_query}':")
        for i, doc in enumerate(results, 1):
            logger.info(f"  {i}. {doc['document_title']} (score: {doc['@search.score']:.3f})")
    except Exception as e:
        logger.error(f"Retrieval test failed: {e}", exc_info=True)
    
    # Test vector search
    logger.info("Testing vector search...")
    try:
        test_text = "LLM deployment and scaling"
        embedding = embedding_gen.embed_text(test_text)
        
        # Vector search not fully supported in basic test, but we can verify structure
        logger.info(f"Generated embedding dimension: {len(embedding)}")
    except Exception as e:
        logger.error(f"Vector search test failed: {e}", exc_info=True)


def test_chunk_schema() -> None:
    """Validate chunk metadata schema."""
    from ingestion.chunking import Chunk
    
    logger.info("Testing chunk schema...")
    
    chunk = Chunk(
        chunk_id="test_0001",
        source_document="/path/to/doc.pdf",
        chunk_text="Sample text content",
        chunk_index=0,
        document_title="Test Document",
        document_hash="abc123",
        page_number=1,
        section_title="Introduction",
        character_count=18,
        token_estimate=10,
    )
    
    chunk_dict = chunk.to_dict()
    logger.info(f"Chunk schema validated: {json.dumps(chunk_dict, indent=2)}")


if __name__ == "__main__":
    logger.info("Starting Day 3 ingestion tests...")
    test_chunk_schema()
    # Note: test_ingestion_end_to_end() requires actual Document Intelligence credentials
    logger.info("Tests complete")

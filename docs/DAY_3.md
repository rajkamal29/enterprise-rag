# Day 3 - Document Ingestion Pipeline + Azure AI Search Indexing

Goal: Build production ingestion from raw documents to searchable Azure AI Search index.

## Outcomes
- Azure Document Intelligence parses PDFs, Word docs, HTML.
- Semantic chunking strategy with configurable chunk size and overlap.
- Embeddings generated via Azure OpenAI (text-embedding-3-large).
- Azure AI Search index schema: vector field + keyword field + metadata.
- Ingestion pipeline with idempotent upsert (re-running is safe).

## Azure Services Used
| Service | Role |
|---|---|
| Azure Document Intelligence | Extract text from PDF, DOCX, HTML |
| Azure OpenAI Embeddings | text-embedding-3-large (3072 dims) |
| Azure AI Search | Index storage + retrieval |

## 6-Hour Plan
1. Implement `DocumentLoader` using Azure Document Intelligence SDK.
2. Implement chunking: fixed-size with overlap + sentence-boundary aware.
3. Implement `EmbeddingService` wrapping Azure OpenAI embeddings with retry.
4. Design Azure AI Search index schema (vector, keyword, metadata fields).
5. Implement `IndexWriter` with upsert logic (document_id as key).
6. Add smoke tests — ingest 3 sample docs, verify they are searchable.

## Index Schema Design
```json
{
  "fields": [
    {"name": "id", "type": "Edm.String", "key": true},
    {"name": "content", "type": "Edm.String", "searchable": true},
    {"name": "content_vector", "type": "Collection(Edm.Single)", "dimensions": 3072},
    {"name": "source", "type": "Edm.String", "filterable": true},
    {"name": "page", "type": "Edm.Int32", "filterable": true}
  ]
}
```

## Exit Criteria
- 3 sample documents indexed into Azure AI Search.
- Keyword search and vector search both return results.
- Ingestion is idempotent (run twice, no duplicates).

## Suggested Commit
feat(day-3): document ingestion pipeline with Azure Document Intelligence and AI Search

## LinkedIn Prompt
Best practice #3 for Enterprise Agentic RAG on Azure: Use Azure Document Intelligence for ingestion — not raw PDF parsers. It handles tables, forms, and multi-column layouts that break naive text extraction. Your retrieval quality is only as good as your parsed content.

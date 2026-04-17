# Day 3 - Shared Ingestion and Retrieval Foundation

Goal: Build the shared document and retrieval layer consumed by both the AI Foundry workflow and the custom Azure agent.

## Outcomes
- Azure Document Intelligence pipeline for PDFs, DOCX, and HTML.
- Common chunking, metadata, and embedding strategy.
- Azure AI Search index schema reusable by both tracks.
- Idempotent ingestion and searchable sample corpus.

## Why this day is shared
- Track A needs a reliable retrieval corpus connected into AI Foundry.
- Track B needs the same corpus for LangGraph and custom tools.

## 6-Hour Plan
1. Implement document parsing with Azure Document Intelligence.
2. Define chunking strategy and metadata contract shared by both tracks.
3. Generate embeddings with Azure OpenAI.
4. Create Azure AI Search index with vector, text, and metadata fields.
5. Build idempotent ingestion and reindexing flow.
6. Validate retrieval from both plain SDK calls and AI Foundry-connected resources.

## Exit Criteria
- Sample corpus indexed once and queryable from both tracks.
- Chunk schema and metadata format documented.
- Re-ingestion produces no duplicates.

## Suggested Commit
feat(day-3): build shared ingestion and retrieval foundation for both tracks

## LinkedIn Prompt
Best practice #3 for Agentic RAG on Azure: treat ingestion as a platform asset, not app-specific code. One clean corpus should serve both AI Foundry workflows and custom agent runtimes.

# Enterprise Agentic RAG on Azure

Production-grade Agentic RAG portfolio project covering both Azure AI Foundry end-to-end workflows and Azure-based custom agent architecture. Designed as an enterprise architecture reference for Solution Architects, Azure Cloud Architects, and AI Architects.

## Current state

| Day | Status | Scope |
|---|---|---|
| Day 1 | ✅ Complete | Repo scaffold, CI/CD (ruff, mypy, pytest, bandit, pip-audit, CodeQL), input guardrails, circuit breaker, pre-commit hooks |
| Day 2 | ✅ Complete | Azure infrastructure (Bicep): AI Foundry, Azure OpenAI, AI Search, Key Vault, Document Intelligence, Storage, Managed Identity; `AzureSettings`, `AzureClientFactory` |
| Day 3 | ✅ Complete | Shared ingestion pipeline: `DocumentParser` (Document Intelligence), `ChunkingStrategy` (paragraph-aware), `EmbeddingGenerator` (text-embedding-3-large), `SearchIndexer` (HNSW), `IngestionPipeline` (SHA256 idempotence, content-change detection, structured logging) |
| Day 4+ | 🔜 Pending | See `EXECUTION_PLAN.md` and `docs/DAY_4.md` |

## Architecture

Two parallel delivery tracks built on shared infrastructure:

- **Track A** — Azure AI Foundry end-to-end: managed agent workflow, Prompt Flow, AI Foundry evaluations
- **Track B** — Custom Azure-based: LangGraph ReAct agent, Azure OpenAI tool-calling, Azure AI Search hybrid retrieval

### Azure services deployed

| Service | Resource | Purpose |
|---|---|---|
| Azure OpenAI | `oai-erag2-dev` | GPT-4o (chat) + text-embedding-3-large (embeddings) |
| Azure AI Search | `srch-erag2-dev` | S1, HNSW vector + BM25 hybrid retrieval |
| Azure AI Foundry | `hub-erag2-dev` / `proj-erag2-dev` | Managed agent workflow surface |
| Document Intelligence | `di-erag2-dev` | PDF/DOCX parsing with layout extraction |
| Key Vault | `kv-erag2-dev` | Secrets management |
| Managed Identity | `id-erag2-dev` | Zero-secret credential for all services |

## Quick start

```bash
# Install dependencies
uv sync

# Run quality checks
uv run ruff check .
uv run mypy src
uv run pytest

# Run ingestion end-to-end test (requires .env with Azure endpoints)
uv run python src/test_ingestion_e2e.py
```

## Repository layout

```
src/
  config/          # AzureSettings (Pydantic), logging_config (structured + correlation ID)
  azure_clients/   # AzureClientFactory — single DefaultAzureCredential for all clients
  guardrails/      # InputValidator, CircuitBreaker
  ingestion/       # DocumentParser, ChunkingStrategy, EmbeddingGenerator,
                   # SearchIndexer, IngestionPipeline
  cost_model/      # Token and cost tracking utilities
infra/             # Bicep modules for all Azure services
docs/              # Day guides (DAY_1.md … DAY_10.md), ADRs, reference docs
tests/             # Unit tests (pytest)
data/
  sample_documents/  # HTML, TXT corpus for ingestion tests
```

## Key documents

- `EXECUTION_PLAN.md` — 10-day delivery plan
- `DAILY_CHECKLIST.md` — day-by-day task tracking
- `docs/ARCHITECTURE_DECISIONS.md` — all ADRs
- `docs/INGESTION_OPTIONS_REFERENCE.md` — parse/chunk/embed/index options with trade-offs
- `docs/WHY_EXPLICIT_INGESTION_PIPELINE.md` — why explicit pipeline over Azure Integrated Vectorization

## Delivery tracks
- Track A: Azure AI Foundry end-to-end Agentic RAG
- Track B: Azure-based custom Agentic RAG with LangGraph and Azure services
- Day 10: refresh all topics with when-to-use-what, tradeoffs, and architecture guidance

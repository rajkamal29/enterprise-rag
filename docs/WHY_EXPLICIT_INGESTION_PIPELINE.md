# Why We Use an Explicit Ingestion Pipeline Instead of Azure AI Search Integrated Vectorization

## Short Answer

**Azure AI Search IS used** — as the vector store and retrieval engine.
What is NOT used is its optional managed ingestion feature called
**Integrated Vectorization**, which lets Azure handle parsing, chunking,
embedding, and indexing automatically.

This document explains why that feature was deliberately bypassed and where
to find every relevant decision in the code.

---

## What Integrated Vectorization Does

Azure AI Search can manage the entire ingest flow internally:

```
Blob Storage → Indexer → Document Intelligence Skill → Text Split Skill
           → Azure OpenAI Embedding Skill → Index (automatic)
```

Zero Python ingestion code. Configured entirely in portal JSON skillsets.
Can be scheduled for incremental updates.

Reference: [Azure AI Search Integrated Vectorization](https://learn.microsoft.com/azure/search/vector-search-integrated-vectorization)

---

## Why It Was Not Used

### Reason 1 — The `Chunk` Dataclass Is the Shared Contract Across Both Tracks

**File**: `src/ingestion/chunking.py`

```python
@dataclass
class Chunk:
    chunk_id: str
    source_document: str
    chunk_text: str
    chunk_index: int
    document_title: str
    document_hash: str        # SHA256[:12] — not in managed skillset output
    page_number: Optional[int]
    section_title: Optional[str]
    character_count: int
    token_estimate: int       # int(char_count / 4) + 50 — not in managed output
```

Track A (AI Foundry Prompt Flow) and Track B (LangGraph ReAct agent) both
query the same index and expect identical field names and types. Azure's
managed skillset outputs a fixed schema — you cannot add `document_hash`,
`token_estimate`, or `chunk_index` without writing the same custom code
anyway. By owning the pipeline, the schema is enforced at the dataclass level
and both tracks are guaranteed to see consistent metadata.

---

### Reason 2 — Idempotence via SHA256 Content Hash

**File**: `src/ingestion/ingestion_pipeline.py`

```python
doc_hash = self._compute_file_hash(doc_path)   # SHA256, read in 8 KB blocks
if doc_hash in self.ingested_documents:
    stats["skipped_documents"] += 1
    continue   # already indexed — skip entirely
```

Azure's built-in indexer deduplicates by **change-tracking**: file
modification timestamps or ETags in Blob Storage. A document with identical
content but a different timestamp will be re-processed and billed again.

SHA256 content hashing skips a document if and only if its bytes have not
changed — regardless of metadata. This is more reliable and significantly
cheaper at scale.

State is persisted to `.ingestion_state.json` — `{ hash: file_path }`.

---

### Reason 3 — Paragraph-Aware Chunking

**File**: `src/ingestion/chunking.py`

```python
paragraphs = content.split("\n\n")          # respect semantic boundaries first
# accumulate until > chunk_size, then:
overlap = _extract_overlap(current_chunk, 128)   # trim to nearest sentence
```

Azure's built-in **Text Split** skill supports only:
- Fixed character count split
- Fixed page split

It does not respect paragraph boundaries (`\n\n`) and cannot trim overlap to
a sentence boundary. Chunks that cut mid-sentence pass fragmented context to
the LLM, measurably degrading faithfulness scores in RAGAS evaluation.

Reference: [Azure AI Search Text Split Skill](https://learn.microsoft.com/azure/search/cognitive-search-skill-textsplit)

---

### Reason 4 — Configuration Is Version-Controlled

Chunking parameters are in source code:

```python
# chunking.py
ChunkingStrategy(chunk_size=1024, chunk_overlap=128, separator="\n\n")
```

With Integrated Vectorization, these live in a portal JSON skillset
definition. You cannot `git diff` a portal change, include it in a pull
request review, roll it back with `git revert`, or unit-test it. The
explicit pipeline means every ingestion decision is reviewable, testable,
and auditable.

---

### Reason 5 — Portability: Not Locked to Azure Blob Storage

Integrated Vectorization requires documents to be in **Azure Blob Storage**
as the data source. The explicit pipeline accepts any file path:

```python
# ingestion_pipeline.py
pipeline.ingest_documents([
    "data/sample_documents/azure-ai-foundry.html",
    "/any/local/path/document.pdf",
    # future: S3 URI, SharePoint export, database blob...
])
```

Switching document sources requires no changes to chunking, embedding, or
indexing code.

---

## When Integrated Vectorization IS the Right Choice

Use it when your project has all of these characteristics:

| Condition | Why it matters |
|---|---|
| Documents already in Azure Blob Storage | Required data source |
| Single consumer (no cross-track schema contract) | No shared `Chunk` dataclass needed |
| Default metadata fields are sufficient | No custom fields needed |
| Scheduled incremental indexing is valuable | Built-in scheduler |
| Change-tracking deduplication is acceptable | Timestamp-based, not content-based |
| Portal configuration is acceptable | No IaC or Git diff requirement |

---

## Side-by-Side Comparison

| Dimension | Integrated Vectorization | This Project's Pipeline |
|---|---|---|
| Chunking logic | Azure fixed-char split | Paragraph-aware, sentence-boundary overlap |
| Metadata schema | Azure fixed fields | Custom `Chunk` dataclass |
| Deduplication | Change-tracking (timestamp / ETag) | SHA256 content hash |
| Config location | Portal JSON skillset | Python source, Git |
| Cross-track consistency | Not guaranteed | Enforced by shared dataclass |
| Document source | Blob Storage only | Any `Path` or local file |
| Code to maintain | None | ~600 lines |
| Upgrade path (layout model) | Portal skillset update | One-line change in `document_parser.py` |

---

## Relevant Source Files

| File | Role |
|---|---|
| [src/ingestion/chunking.py](../src/ingestion/chunking.py) | `Chunk` dataclass + paragraph-aware algorithm |
| [src/ingestion/ingestion_pipeline.py](../src/ingestion/ingestion_pipeline.py) | SHA256 idempotence, end-to-end orchestration |
| [src/ingestion/search_indexer.py](../src/ingestion/search_indexer.py) | Index schema, HNSW config, document upload |
| [src/ingestion/embeddings.py](../src/ingestion/embeddings.py) | Batch embedding via AOAI text-embedding-3-large |
| [src/ingestion/document_parser.py](../src/ingestion/document_parser.py) | Azure Document Intelligence parsing |

---

## Reference Links

- [Azure AI Search Integrated Vectorization Overview](https://learn.microsoft.com/azure/search/vector-search-integrated-vectorization)
- [Azure AI Search Indexer Overview](https://learn.microsoft.com/azure/search/search-indexer-overview)
- [Azure AI Search Built-in Skills (Text Split, Embedding)](https://learn.microsoft.com/azure/search/cognitive-search-predefined-skills)
- [Azure AI Search Text Split Skill](https://learn.microsoft.com/azure/search/cognitive-search-skill-textsplit)
- [Azure AI Search AzureOpenAIEmbeddingSkill](https://learn.microsoft.com/azure/search/cognitive-search-skill-azure-openai-embedding)
- [Azure AI Search Change Tracking & Deletion Detection](https://learn.microsoft.com/azure/search/search-howto-index-changed-deleted-blobs)
- [Azure AI Search Index Schema Design](https://learn.microsoft.com/azure/search/search-what-is-an-index)
- [Chunking strategies for RAG (Pinecone)](https://www.pinecone.io/learn/chunking-strategies/)
- [RAGAS: Retrieval-Augmented Generation Assessment](https://docs.ragas.io)

---

*See also: [INGESTION_OPTIONS_REFERENCE.md](./INGESTION_OPTIONS_REFERENCE.md) for the full trade-off comparison across all four pipeline stages (parse, chunk, embed, index).*

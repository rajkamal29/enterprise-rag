# Ingestion Pipeline: Options, Trade-offs & Decisions

A comprehensive reference for every stage of the RAG ingestion pipeline —
parsing, chunking, embedding, and indexing. Each section lists all viable
options, a decision summary, and reference links for deeper reading.

This document records the rationale behind choices made in this project and
serves as a guide for future upgrades or LinkedIn content.

---

## Stage 1: PARSE — Extracting Text from Documents

### What This Project Uses
**Azure Document Intelligence** (`prebuilt-document` model) for PDF and DOCX.
Plain regex stripping for HTML files.

```python
poller = self.client.begin_analyze_document("prebuilt-document", f)
result = poller.result()
return result.content   # fallback: result.paragraphs
```

---

### Option A — Azure Document Intelligence ✅ Used Here

Managed cloud OCR + layout analysis service. Understands PDFs (including
scanned), DOCX, tables, forms, and 100+ formats. Returns structured content
with page numbers, paragraphs, and tables.

| Pros | Cons |
|---|---|
| Handles scanned PDFs (OCR) | API cost (~$1.50 / 1000 pages) |
| Extracts tables, headers, layout | Requires network call per document |
| Supports 100+ file types | Azure-only |
| Managed, no library to maintain | Adds latency vs local parsers |

**Models available inside Document Intelligence:**

| Model | What it extracts | Cost |
|---|---|---|
| `prebuilt-read` | Pure text, fastest | Lowest |
| `prebuilt-document` | Text + key-value pairs | Medium ← **used here** |
| `prebuilt-layout` | Headers, sections, tables, reading order | Higher |
| `prebuilt-invoice` / `prebuilt-receipt` | Domain-specific forms | Medium |

> **Upgrade path**: Switch to `prebuilt-layout` to populate `section_title`
> in the `Chunk` dataclass. That field is already wired as `None` — one line
> change in `document_parser.py`.

---

### Option B — PyMuPDF / PyPDF2 (local, free)

Pure Python PDF parsing. No OCR, no tables. Works fully offline.

```python
import fitz  # PyMuPDF
doc = fitz.open("file.pdf")
text = "\n".join(page.get_text() for page in doc)
```

| Pros | Cons |
|---|---|
| Free, no API cost | Fails on scanned PDFs (no OCR) |
| Offline, no latency | No table or layout extraction |
| Fast | No reading-order intelligence |

**When to use**: Developer environments, CI pipelines, text-only PDFs.

---

### Option C — Apache Tika (local server)

Java-based parser covering 1000+ formats via REST. Industry standard for
on-premise enterprise content pipelines.

| Pros | Cons |
|---|---|
| 1000+ formats supported | Requires Java + running server |
| Free and open source | Complex setup |
| Handles email, Office, PDF | No OCR capability |

**When to use**: On-premise environments, extreme format diversity.

---

### Option D — Unstructured.io

Open-source Python library (and cloud API) built specifically for RAG
pipelines. Partitions documents into typed elements (Title, NarrativeText,
Table, Image).

```python
from unstructured.partition.auto import partition
elements = partition("document.pdf")
# elements are typed: Title, NarrativeText, Table, ListItem...
```

| Pros | Cons |
|---|---|
| RAG-native typed output | Slower than PyMuPDF |
| Auto-detects document format | Some features require paid API |
| Handles HTML, emails, Slack exports | Large dependency tree |
| Element types aid chunking decisions | |

**When to use**: Mixed-format corpora where semantic element type matters
(e.g. keep tables separate from prose).

---

### Option E — LlamaIndex / LangChain Loaders

Framework-native document loaders that wrap the options above and normalize
output into framework objects.

```python
# LlamaIndex
from llama_index.core import SimpleDirectoryReader
documents = SimpleDirectoryReader("data/").load_data()

# LangChain
from langchain_community.document_loaders import PyMuPDFLoader
docs = PyMuPDFLoader("file.pdf").load()
```

| Pros | Cons |
|---|---|
| 100+ ready-made loaders | Framework lock-in |
| Pre-built for RAG pipelines | Less control over raw metadata |
| Large community ecosystem | Abstraction hides important details |

**When to use**: Rapid prototyping or framework-first projects.

---

### Parse Decision Summary

| Scenario | Recommended Option |
|---|---|
| Enterprise docs, scanned PDFs | **Azure Document Intelligence** ✅ |
| Text-only PDFs, local/offline | PyMuPDF |
| 100+ format variety, on-prem | Apache Tika |
| Mixed formats, element-typed output | Unstructured.io |
| Framework-first prototyping | LlamaIndex / LangChain Loaders |

**Why Document Intelligence here**: Enterprise documents are frequently
scanned. The `prebuilt-layout` upgrade to populate `section_title` is
pre-designed into the `Chunk` dataclass. Integrates cleanly with existing
Managed Identity + `AzureClientFactory` pattern with no extra credentials.

---

### Parse Reference Links

- [Azure Document Intelligence Overview](https://learn.microsoft.com/azure/ai-services/document-intelligence/overview)
- [Document Intelligence Model Overview](https://learn.microsoft.com/azure/ai-services/document-intelligence/concept-model-overview)
- [prebuilt-layout model](https://learn.microsoft.com/azure/ai-services/document-intelligence/concept-layout)
- [PyMuPDF Documentation](https://pymupdf.readthedocs.io)
- [PyPDF2 / pypdf GitHub](https://github.com/py-pdf/pypdf)
- [Unstructured.io](https://unstructured.io)
- [Unstructured GitHub](https://github.com/Unstructured-IO/unstructured)
- [LlamaIndex Document Loaders](https://docs.llamaindex.ai/en/stable/module_guides/loading/)
- [LangChain Document Loaders](https://python.langchain.com/docs/how_to/#document-loaders)

---

## Stage 2: CHUNK — Splitting Documents into Retrieval Units

### What This Project Uses
**Paragraph-aware fixed-size chunking** — 1024 chars, 128-char overlap,
`\n\n` paragraph separator, with sentence-boundary overlap trimming.

```python
# Split by paragraph boundaries first
paragraphs = content.split("\n\n")

for para in paragraphs:
    if len(current_chunk + para) > 1024:
        save(current_chunk)
        # trim overlap to nearest sentence boundary
        overlap = _extract_overlap(current_chunk, 128)
        current_chunk = overlap + para
    else:
        current_chunk += para
```

---

### Strategy A — Fixed Character Split

Split every N characters, no awareness of content structure.

```python
chunks = [text[i:i+1024] for i in range(0, len(text), 1024)]
```

| Pros | Cons |
|---|---|
| Trivial to implement | Mid-sentence and mid-word cuts |
| Fastest | Hurts LLM answer quality |
| Predictable chunk sizes | No semantic coherence |

---

### Strategy B — Fixed Token Split

Same as A but counts tokens using `tiktoken` instead of characters. More
accurate for LLM context window management.

```python
import tiktoken
enc = tiktoken.get_encoding("cl100k_base")
tokens = enc.encode(text)
chunks = [enc.decode(tokens[i:i+512]) for i in range(0, len(tokens), 512)]
```

| Pros | Cons |
|---|---|
| Accurate for LLM context windows | Still splits mid-sentence |
| Works correctly across languages | `tiktoken` dependency |

---

### Strategy C — Paragraph-Aware Split ✅ Used Here

Split at semantic boundaries (`\n\n`). Fall back to size limit only when a
single paragraph exceeds the target. Overlap extracted at sentence boundary.

| Pros | Cons |
|---|---|
| Preserves semantic coherence | Uneven chunk sizes |
| No extra dependencies | Very long paragraphs can exceed limit |
| Best quality for prose documents | |

---

### Strategy D — Recursive Character Split (LangChain standard)

Try separators in order: `\n\n` → `\n` → `. ` → ` ` → characters.
Falls back progressively until size fits.

```python
from langchain.text_splitter import RecursiveCharacterTextSplitter
splitter = RecursiveCharacterTextSplitter(chunk_size=1024, chunk_overlap=128)
chunks = splitter.split_text(text)
```

| Pros | Cons |
|---|---|
| Very robust, rarely mid-word | LangChain dependency |
| Works on code, prose, markdown | Slightly more complex |
| De facto standard in LangChain ecosystem | |

**When to use**: Mixed content (code + prose + markdown). Best default if
you are already using LangChain.

---

### Strategy E — Semantic Chunking

Use sentence embeddings to detect topic shifts. Group sentences until
semantic similarity drops below threshold.

```python
from semantic_chunkers import StatisticalChunker
chunker = StatisticalChunker(encoder=encoder)
chunks = chunker(docs=["Your long document..."])
```

| Pros | Cons |
|---|---|
| Best semantic coherence | Requires embedding model at ingest time |
| Chunks are topically complete | 2–5x slower than fixed-size |
| Dramatically improves retrieval precision | Unpredictable chunk sizes |

**When to use**: High-value corpora where retrieval precision is critical
and extra compute cost is acceptable.

---

### Strategy F — Document Structure / Hierarchical (Upgrade Path)

Use `prebuilt-layout` model to extract real document sections (H1, H2,
paragraphs, tables) as structurally-aware chunks with `section_title`
populated.

```python
# One-line upgrade in document_parser.py:
poller = client.begin_analyze_document("prebuilt-layout", f)
# result.sections provides H1 > H2 > paragraph hierarchy
# → populates Chunk.section_title
```

| Pros | Cons |
|---|---|
| Preserves real document structure | Requires layout model (higher cost) |
| `section_title` is semantically meaningful | API-dependent |
| Best for technical / structured documents | |

> The `Chunk` dataclass already has `section_title: Optional[str] = None`
> reserved for this upgrade. Nothing else changes.

---

### Strategy G — Sentence Window / Small-to-Big

Store small sentence-level chunks for precise retrieval, but return the
surrounding larger window of context to the LLM.

```
Index:  individual sentences (small — high precision retrieval)
Return: ±3 surrounding sentences (window — full context for LLM)
```

| Pros | Cons |
|---|---|
| High retrieval precision | Two-pass retrieval complexity |
| LLM gets full surrounding context | More moving parts in query pipeline |
| Used natively in LlamaIndex | Double storage |

---

### Chunk Size Guidance

| Use Case | Chunk Size | Overlap |
|---|---|---|
| Dense technical / API docs | 512 chars | 64 |
| **General prose** | **1024 chars** ← this project | **128** ← this project |
| Long narrative / legal / contracts | 2048 chars | 256 |
| Q&A / FAQ documents | 256 chars | 32 |
| Source code files | Per function / class | 0 |

---

### Chunk Decision Summary

| Scenario | Recommended Strategy |
|---|---|
| Prose, no extra dependencies | **Paragraph-aware** ✅ (this project) |
| Mixed content (code + prose + markdown) | Recursive Character Split |
| Best possible retrieval quality | Semantic Chunking |
| Structured document with headings | Hierarchical / Layout model |
| High precision + full context to LLM | Sentence Window |

---

### Chunk Reference Links

- [Pinecone: Chunking Strategies (comprehensive guide)](https://www.pinecone.io/learn/chunking-strategies/)
- [Chroma: Evaluating Chunking](https://research.trychroma.com/evaluating-chunking)
- [Semantic Chunking Paper (arXiv)](https://arxiv.org/abs/2312.09571)
- [LangChain RecursiveCharacterTextSplitter](https://python.langchain.com/docs/how_to/recursive_text_splitter/)
- [LlamaIndex Sentence Window Node Parser](https://docs.llamaindex.ai/en/stable/examples/node_postprocessor/MetadataReplacementDemo/)
- [tiktoken (OpenAI tokenizer)](https://github.com/openai/tiktoken)
- [Semantic Chunkers library](https://github.com/aurelio-labs/semantic-chunkers)

---

## Stage 3: EMBED — Converting Text to Vectors

### What This Project Uses
**Azure OpenAI `text-embedding-3-large`** — 3072 dimensions, batch size 20.

```python
response = self.client.embeddings.create(
    input=batch,           # up to 20 texts per call
    model="text-embedding-3-large",
)
# response.data[i].embedding = list[float], 3072 values
# sorted by item.index to preserve order
```

---

### Option A — text-embedding-3-large ✅ Used Here

| Dimension | Max Tokens | Cost | Notes |
|---|---|---|---|
| 3072 (reducible) | 8191 | ~$0.13 / 1M tokens | Highest quality OpenAI model |

| Pros | Cons |
|---|---|
| Highest quality on MTEB benchmark | Highest API cost in AOAI lineup |
| Managed, no GPU needed | Azure deployment required |
| MRL: reduce to 256–1024D with ~5% loss | |
| Native Azure integration | |

**Matryoshka Representation Learning (MRL)**: Embed once at 3072D. Query at
any lower dimension (256, 512, 1024) without re-embedding. Trade ~5% quality
for 10x storage reduction.

```python
# Future: reduce index storage with minimal quality loss
response = client.embeddings.create(
    input=text,
    model="text-embedding-3-large",
    dimensions=1024    # MRL reduction
)
```

---

### Option B — text-embedding-3-small

| Dimension | Cost | vs Large |
|---|---|---|
| 1536 | ~$0.02 / 1M tokens | 6.5x cheaper, ~3% less accurate |

**When to use**: Cost-sensitive projects with large corpora where a small
quality trade-off is acceptable.

---

### Option C — text-embedding-ada-002 (legacy)

| Dimension | Cost | Status |
|---|---|---|
| 1536 | ~$0.10 / 1M tokens | Legacy — superseded |

**When to use**: Do not use for new projects. Use `text-embedding-3-small`
instead. Kept only for backward compatibility with existing indexes.

---

### Option D — Sentence Transformers (open-source, local)

Run embedding models locally on your own hardware. Zero API cost.

```python
from sentence_transformers import SentenceTransformer
model = SentenceTransformer("BAAI/bge-large-en-v1.5")
embeddings = model.encode(texts, batch_size=32)
```

**Top models on MTEB leaderboard:**

| Model | Dimensions | Notes |
|---|---|---|
| `BAAI/bge-large-en-v1.5` | 1024 | Best open-source English general |
| `BAAI/bge-m3` | 1024 | Best open-source multilingual |
| `intfloat/e5-large-v2` | 1024 | Strong retrieval tasks |
| `nomic-ai/nomic-embed-text-v1.5` | 768 | MRL support, MIT license |

| Pros | Cons |
|---|---|
| Zero API cost | Requires GPU for production throughput |
| Data never leaves your environment | You manage model upgrades |
| Full control | CPU inference is slow |
| Open source, permissive licences | |

---

### Option E — Cohere Embed v3

Commercial embedding API. Best-in-class multilingual support.

| Model | Dimensions | Notes |
|---|---|---|
| `embed-english-v3.0` | 1024 | Strong English retrieval |
| `embed-multilingual-v3.0` | 1024 | Best multilingual option |

**When to use**: Multilingual enterprise RAG where Azure OpenAI multilingual
quality is insufficient.

---

### Option F — Azure AI Search Integrated Vectorization

Let Azure AI Search call your AOAI embedding deployment automatically via a
skillset. Zero embedding code required.

```json
{
  "@odata.type": "#Microsoft.Skills.Text.AzureOpenAIEmbeddingSkill",
  "resourceUri": "https://oai-erag2-dev.openai.azure.com/",
  "deploymentId": "text-embedding-3-large"
}
```

| Pros | Cons |
|---|---|
| Zero ingestion code | Loses custom metadata contract |
| Managed by Azure | No cross-track consistency guarantee |
| Scheduling and incremental updates | No document-hash deduplication |
| | Config lives in portal, not Git |

**Why not used here**: Loses the shared `Chunk` metadata contract, document
hash idempotence, and cross-track consistency (Track A + Track B must see
identical schemas).

---

### Embed Decision Summary

| Scenario | Recommended Option |
|---|---|
| Highest quality, Azure-native | **text-embedding-3-large** ✅ (this project) |
| Cost-sensitive, still high quality | text-embedding-3-small |
| Private data, no API cost | BAAI/bge-large-en-v1.5 (Sentence Transformers) |
| Multilingual enterprise | bge-m3 or Cohere embed-multilingual-v3 |
| Existing index, legacy compat | ada-002 (migration candidate) |
| Zero code, managed pipeline | Integrated Vectorization |

---

### Embed Reference Links

- [MTEB Leaderboard (live benchmark)](https://huggingface.co/spaces/mteb/leaderboard)
- [OpenAI: New Embedding Models (MRL explained)](https://openai.com/blog/new-embedding-models-and-api-updates)
- [Azure OpenAI Embedding Models](https://learn.microsoft.com/azure/ai-services/openai/concepts/models#embeddings)
- [Sentence Transformers (sbert.net)](https://sbert.net)
- [BAAI/bge-large-en-v1.5 on HuggingFace](https://huggingface.co/BAAI/bge-large-en-v1.5)
- [Cohere Embed v3](https://cohere.com/blog/introducing-embed-v3)
- [Azure Search Integrated Vectorization](https://learn.microsoft.com/azure/search/vector-search-integrated-vectorization)
- [Matryoshka Representation Learning Paper](https://arxiv.org/abs/2205.09788)

---

## Stage 4: INDEX — Storing and Searching Vectors

### What This Project Uses
**Azure AI Search** with **HNSW algorithm**, hybrid retrieval schema
(BM25 keyword + vector cosine), filterable metadata fields.

```python
SearchField(
    name="embedding",
    type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
    vector_search_dimensions=3072,
    vector_search_profile_name="my-vector-config",   # → HNSW
)
HnswAlgorithmConfiguration(name="my-hnsw")
```

---

### Option A — Azure AI Search (HNSW) ✅ Used Here

Managed enterprise vector + keyword + hybrid search. SLA-backed.

**Search modes available in this index:**

| Mode | Mechanism | Best For |
|---|---|---|
| Keyword (BM25) | TF-IDF term frequency | Exact terms, names, codes |
| Vector | Cosine similarity on embeddings | Semantic meaning |
| Hybrid | BM25 + Vector combined via RRF | Best of both worlds |
| Semantic Ranker | Cross-encoder re-ranking of top-N | Highest precision (extra cost) |

**HNSW Algorithm internals:**
- Builds a multi-layer proximity graph at index time
- At query: traverses graph layers to find approximate nearest neighbours
- Orders of magnitude faster than brute-force cosine over all documents
- Configurable parameters:
  - `m` — connections per node (higher = better recall, more memory)
  - `efConstruction` — build accuracy
  - `efSearch` — query accuracy vs speed

| Pros | Cons |
|---|---|
| Fully managed, 99.9% SLA | Cost: S1 ~$250/month |
| Hybrid search (BM25 + vector) built-in | Azure-only |
| Semantic Ranker available add-on | |
| Tight AI Foundry integration | |
| Filterable metadata on all fields | |
| REST + SDK APIs | |

---

### Option B — pgvector (PostgreSQL extension)

Add vector search to an existing Postgres database. Available on Azure
Database for PostgreSQL – Flexible Server.

```sql
CREATE EXTENSION vector;
CREATE TABLE chunks (
    id TEXT PRIMARY KEY,
    embedding VECTOR(3072),
    chunk_text TEXT,
    document_title TEXT
);
CREATE INDEX ON chunks USING hnsw (embedding vector_cosine_ops);
SELECT id FROM chunks ORDER BY embedding <=> '[...]' LIMIT 5;
```

| Pros | Cons |
|---|---|
| Reuse existing Postgres infra | Not as fast as dedicated vector DBs |
| Full SQL on metadata (JOINs, filters) | Needs manual index tuning |
| Transactional consistency with other data | HNSW support added only recently |
| Familiar tooling | |

**When to use**: You already have Azure PostgreSQL and want vector search
without a new service. Small to medium corpora (<10M vectors).

---

### Option C — Qdrant

Purpose-built open-source vector database with the richest filtering
capabilities of any vector DB.

```python
from qdrant_client import QdrantClient
client = QdrantClient("localhost", port=6333)
client.upsert(collection_name="chunks", points=[
    PointStruct(id=1, vector=embedding, payload={"text": "...", "title": "..."})
])
results = client.search("chunks", query_vector=embedding, limit=5,
                        query_filter=Filter(must=[FieldCondition(key="title", ...])))
```

| Pros | Cons |
|---|---|
| Best-in-class payload filtering | Self-managed (or Qdrant Cloud) |
| Fast, memory-efficient HNSW | Extra infrastructure to operate |
| Sparse + dense hybrid search | |
| Scalar and binary quantization | |
| Open source (Apache 2.0) | |

---

### Option D — Chroma

Lightweight, embeddable vector DB. Zero infrastructure. Built for local dev
and small corpora.

```python
import chromadb
client = chromadb.Client()
collection = client.create_collection("chunks")
collection.add(documents=texts, embeddings=vectors, ids=ids)
results = collection.query(query_embeddings=[query_vec], n_results=5)
```

| Pros | Cons |
|---|---|
| Zero infrastructure, in-process | Not production-scale |
| Simple Python API | Limited filtering |
| Server mode available | No managed option |
| Great for notebooks and prototyping | |

---

### Option E — FAISS (Facebook AI Similarity Search)

Highly optimized C++ library with Python bindings. Used as the search engine
inside many higher-level frameworks.

```python
import faiss
import numpy as np

index = faiss.IndexHNSWFlat(3072, 32)  # 3072D, m=32
index.add(np.array(embeddings, dtype=np.float32))
distances, indices = index.search(np.array([query_vec]), k=5)
```

| Pros | Cons |
|---|---|
| Extremely fast | No persistence by default (manual serialize) |
| GPU acceleration available | No built-in metadata filtering |
| Multiple index types (Flat, IVF, HNSW, PQ) | Manual result-to-document mapping |
| Open source, widely used | |

---

### Option F — Weaviate

Managed + self-hosted vector DB with GraphQL API and strong multi-tenancy.
Good for SaaS applications with tenant-isolated data.

```python
import weaviate
client = weaviate.Client("http://localhost:8080")
client.data_object.create({"text": "...", "title": "..."}, "Chunk",
                          vector=embedding)
```

| Pros | Cons |
|---|---|
| Multi-tenant isolation | GraphQL learning curve |
| Modules (AOAI, Cohere, etc.) | Self-hosting complexity |
| Managed Weaviate Cloud | |

---

### Option G — Pinecone

Fully managed serverless vector DB. Zero infrastructure, pay-per-query.

```python
import pinecone
pc = pinecone.Pinecone(api_key="...")
index = pc.Index("rag-chunks")
index.upsert(vectors=[("id1", embedding, {"text": "...", "title": "..."})])
results = index.query(vector=query_vec, top_k=5, include_metadata=True)
```

| Pros | Cons |
|---|---|
| Zero ops, fully serverless | Vendor lock-in |
| Pay-per-query | Data leaves your environment |
| Fast cold start | Less control vs self-hosted |

---

### Vector Search Algorithm Comparison

| Algorithm | Type | Speed | Recall | Memory | Notes |
|---|---|---|---|---|---|
| **HNSW** ← used here | Graph ANN | ⚡⚡⚡ | ★★★★★ | High | Best recall/speed trade-off |
| IVF-Flat | Cluster ANN | ⚡⚡ | ★★★★ | Medium | Good for large corpora |
| Flat / Brute-force | Exact | ⚡ | ★★★★★ (exact) | Low | Small corpora only |
| IVF-PQ | Compressed ANN | ⚡⚡⚡ | ★★★ | Very low | Memory-constrained |
| ScaNN (Google) | Compressed ANN | ⚡⚡⚡ | ★★★★ | Low | Used in Google Search |

---

### Index Decision Summary

| Scenario | Recommended Option |
|---|---|
| Azure-native, enterprise, hybrid search | **Azure AI Search (HNSW)** ✅ (this project) |
| Existing Postgres, SQL metadata | pgvector |
| Best filtering, self-hosted | Qdrant |
| Local dev, prototyping, notebooks | Chroma |
| Offline, embedded, ultra-fast | FAISS |
| Serverless, zero ops | Pinecone |
| Multi-tenant SaaS | Weaviate |

---

### Index Reference Links

- [Azure AI Search Vector Search Overview](https://learn.microsoft.com/azure/search/vector-search-overview)
- [Azure AI Search Hybrid Search](https://learn.microsoft.com/azure/search/hybrid-search-overview)
- [Azure AI Search Ranking (RRF + Semantic)](https://learn.microsoft.com/azure/search/vector-search-ranking)
- [Azure AI Search Semantic Ranker](https://learn.microsoft.com/azure/search/semantic-search-overview)
- [HNSW Original Paper (arXiv)](https://arxiv.org/abs/1603.09320)
- [ANN Benchmarks (live algorithm comparison)](https://ann-benchmarks.com)
- [pgvector GitHub](https://github.com/pgvector/pgvector)
- [pgvector on Azure PostgreSQL](https://learn.microsoft.com/azure/postgresql/flexible-server/how-to-use-pgvector)
- [Qdrant Documentation](https://qdrant.tech/documentation/)
- [Chroma Documentation](https://docs.trychroma.com)
- [FAISS (Facebook AI)](https://faiss.ai)
- [Weaviate](https://weaviate.io/developers/weaviate)
- [Pinecone Documentation](https://docs.pinecone.io)

---

## Full Pipeline Decision Map

```
PARSE     → Azure Document Intelligence (prebuilt-document)
                ↓ Upgrade path: prebuilt-layout → populates Chunk.section_title

CHUNK     → Paragraph-aware, 1024 chars, 128 overlap, sentence-boundary trim
                ↓ Upgrade path: semantic chunking or hierarchical structure

EMBED     → text-embedding-3-large, 3072D, batch=20, sorted by item.index
                ↓ Upgrade path: MRL reduction to 1024D (<5% quality loss, 3x storage saving)

INDEX     → Azure AI Search, HNSW, hybrid BM25 + vector, filterable metadata
                ↓ Upgrade path: add Semantic Ranker for top-N re-ranking
```

---

## RAG Architecture Reference Links (Broader Reading)

- [Azure RAG Solution Design Guide](https://learn.microsoft.com/azure/architecture/ai-ml/architecture/rag-solution-design-and-evaluation-guide)
- [RAG Survey Paper (arXiv 2312.10997)](https://arxiv.org/abs/2312.10997) — comprehensive survey of all RAG techniques
- [Advanced RAG Techniques Paper (arXiv 2401.15884)](https://arxiv.org/abs/2401.15884)
- [Retrieval-Augmented Generation Original Paper (Lewis et al.)](https://arxiv.org/abs/2005.11401)
- [Azure AI Search + OpenAI RAG Sample](https://github.com/Azure-Samples/azure-search-openai-demo)
- [LlamaIndex RAG Documentation](https://docs.llamaindex.ai/en/stable/getting_started/concepts/)
- [LangChain RAG Tutorial](https://python.langchain.com/docs/tutorials/rag/)

---

*Last updated: Day 3 complete. Next update: Day 4 — AI Foundry Prompt Flow integration.*

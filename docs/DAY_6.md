# Day 6 - Hybrid Retrieval + RAGAS Evaluation Pipeline

Goal: Upgrade to Azure AI Search hybrid retrieval and add RAGAS as a CI evaluation gate.

## Outcomes
- Azure AI Search hybrid query: keyword (BM25) + vector + semantic reranker in one call.
- RAGAS evaluation: faithfulness, answer relevance, context precision scored.
- Evaluation pipeline runs in CI — blocks merge if scores drop below threshold.
- Retrieval quality benchmark: hybrid vs. vector-only documented.

## Azure AI Search Hybrid Query
```python
# One query hits all three retrieval modes simultaneously
results = search_client.search(
    search_text=query,           # BM25 keyword
    vector_queries=[VectorizedQuery(
        vector=embedding,
        fields="content_vector",
        k_nearest_neighbors=50,
    )],
    query_type="semantic",        # Semantic reranker on top
    semantic_configuration_name="default",
    top=5,
)
```

## RAGAS Metrics
| Metric | What it measures | Target |
|---|---|---|
| Faithfulness | Answer is grounded in retrieved context | ≥ 0.85 |
| Answer Relevance | Answer addresses the question | ≥ 0.80 |
| Context Precision | Retrieved chunks are relevant | ≥ 0.75 |

## 6-Hour Plan
1. Implement `HybridRetriever` using Azure AI Search hybrid query.
2. Benchmark: vector-only vs. keyword-only vs. hybrid on 20 test queries.
3. Install RAGAS, define evaluation dataset (query, answer, context triples).
4. Implement evaluation script that outputs metric scores to JSON.
5. Add CI step: run evaluation, fail if any metric below threshold.
6. Document benchmark results in ADR.

## Exit Criteria
- Hybrid retrieval outperforms vector-only by ≥ 10% on context precision.
- RAGAS CI gate blocks a deliberately bad retrieval config.

## Suggested Commit
feat(day-6): hybrid retrieval and RAGAS evaluation CI gate

## LinkedIn Prompt
Best practice #6 for Enterprise Agentic RAG on Azure: Treat retrieval quality as a CI metric. RAGAS gives you faithfulness, relevance, and context precision scores. If your retrieval changes break the score threshold — the pipeline fails. Ship quality gates, not just code gates.

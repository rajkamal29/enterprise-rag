# Architecture Decision Records (ADR)

## ADR-0: Guardrails First
Decision: Build input/output validation and safety checks before advanced RAG features.  
Reason: Prevents prompt injection, bad context, and unsafe responses early.

## ADR-1: Cost-Aware by Design
Decision: Track token and retrieval costs per request from day 2 onward.  
Reason: Production systems fail on cost surprises before they fail on model quality.

## ADR-2: Hybrid Retrieval
Decision: Use BM25 + vector retrieval with fusion, then rerank.  
Reason: Better recall and precision than single-method retrieval.

## ADR-3: Full Observability
Decision: Instrument traces, metrics, and alerts before scaling traffic.  
Reason: Debuggability and SLO confidence are required for interview-grade design.

## ADR-4: Graceful Degradation
Decision: Add fallback cascade (cache -> compact model -> safe response).  
Reason: Preserve user experience during outages and latency spikes.

## ADR-5: Scale by Partitioning
Decision: Prepare shard-aware indexing and caching for 100M docs.  
Reason: Keeps latency and cost bounded at scale.

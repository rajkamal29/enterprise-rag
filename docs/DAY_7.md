# Day 7 - Evaluation, Performance, and Cost Optimization Across Both Tracks

Goal: Measure both tracks rigorously and optimize them for latency, token usage, and retrieval quality.

## Outcomes
- AI Foundry evaluation surface used for Track A.
- RAGAS or custom eval pipeline used for Track B.
- Latency budget and token budget set per request stage.
- Caching, chunk size, top-k, and memory-size tradeoffs measured.

## Optimization themes
| Topic | Questions to answer |
|---|---|
| Performance | Where are the slowest stages in each track? |
| Cost | Which steps dominate token or runtime spend? |
| Retrieval | What top-k and chunking strategy gives best quality per cost? |
| Memory | How much history is enough before accuracy flattens and cost rises? |

## 6-Hour Plan
1. Run AI Foundry evaluations for Track A.
2. Run RAGAS or custom benchmark for Track B.
3. Measure latency per stage and define budget thresholds.
4. Compare chunk size, top-k, cache hit rate, and memory window size.
5. Document cost-performance-quality tradeoffs.
6. Save the comparison inputs for Day 10 refresh.

## Exit Criteria
- Both tracks have measurable quality and latency baselines.
- At least one cost optimization and one latency optimization are implemented.
- Evaluation evidence exists for later architecture guidance.

## Suggested Commit
feat(day-7): add evaluation, performance, and cost optimization for both tracks

## LinkedIn Prompt
Best practice #7 for Agentic RAG on Azure: optimize with evidence, not intuition. Measure chunk size, top-k, memory window, cache hit rate, and token budgets before declaring an architecture better.

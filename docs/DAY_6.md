# Day 6 - Memory, Tools, and Retrieval Optimization Across Both Tracks

Goal: Add memory and tool patterns that work across both implementations, then optimize retrieval quality.

## Outcomes
- Short-term and long-term memory strategy defined for both tracks.
- Shared tool taxonomy for search, date, calculator, and HTTP tasks.
- Hybrid retrieval benchmark across managed and custom flows.
- Retrieval quality improvements documented with reusable metrics.

## 6-Hour Plan
1. Define short-term and long-term memory responsibilities.
2. Add or map tool patterns into both AI Foundry and LangGraph workflows.
3. Implement Azure AI Search hybrid retrieval benchmark.
4. Add caching and memory-size boundaries for performance and cost control.
5. Document how memory differs between managed and custom orchestration.
6. Capture early when-to-use-what guidance for tools and memory.

## Exit Criteria
- Memory approach is documented for both tracks.
- Hybrid retrieval is benchmarked and chosen intentionally.
- Tool and memory tradeoffs are recorded for Day 10 refresh.

## Suggested Commit
feat(day-6): add memory, tools, and retrieval optimization across both tracks

## LinkedIn Prompt
Best practice #6 for Agentic RAG on Azure: memory is not one thing. Keep a strict boundary between session memory, persistent memory, and retrieval context or your cost, latency, and correctness all drift upward.

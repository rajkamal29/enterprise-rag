# Day 5 - Azure-Based Custom Agent Workflow

Goal: Build the custom Azure-based Agentic RAG path using LangGraph and compare it to the AI Foundry workflow.

## Outcomes
- LangGraph ReAct agent with Azure OpenAI tool-calling.
- Azure AI Search tool integration and citation enforcement.
- Custom runtime state model and trace identifiers.
- First explicit comparison between Track A and Track B orchestration style.

## Why this day follows AI Foundry
- Build the managed path first to understand the baseline.
- Build the custom path next to understand where flexibility and control justify extra engineering.

## 6-Hour Plan
1. Implement LangGraph state model and ReAct loop.
2. Add Azure AI Search tool for retrieval.
3. Enforce citations and grounded response pattern.
4. Add request and tool-call tracing IDs.
5. Compare the same use case across Track A and Track B.
6. Document where custom orchestration wins and where it costs more.

## Exit Criteria
- Custom agent answers grounded questions with citations.
- Same sample workload runs in both AI Foundry and custom LangGraph paths.
- Initial managed-vs-custom tradeoffs are documented.

## Suggested Commit
feat(day-5): build Azure-based custom agent workflow with LangGraph

## LinkedIn Prompt
Best practice #5 for Agentic RAG on Azure: after the managed baseline, build the custom path. LangGraph gives you explicit state, routing, and testability when the managed surface is not enough.

## Shipped (Day 5 — 2026-04-18)
- `src/langgraph_agent/state.py` — `AgentState` TypedDict
- `src/langgraph_agent/search_tool.py` — Azure AI Search retrieval tool (field-name fallback for `document_title`/`chunk_text`/`source_document`)
- `src/langgraph_agent/react_agent.py` — LangGraph `StateGraph` ReAct loop with tool-calling
- `src/langgraph_agent/agent.py` — `LangGraphRagAgent` facade matching Track A interface
- `src/compare_tracks.py` — side-by-side runner: same 3 questions through both tracks, `--json-out` and `--csv-out` flags
- `data/track_compare.json` + `data/track_compare.csv` — comparison evidence committed
- `tests/langgraph_agent/` — 6 unit tests
- Commits: `feat(day-5)` + `chore(ingestion)` — CI green, 67 tests passing

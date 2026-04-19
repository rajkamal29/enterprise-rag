# Day 4 - Azure AI Foundry End-to-End Workflow

Goal: Build the first end-to-end Agentic RAG flow inside Azure AI Foundry.

## Outcomes
- AI Foundry project connected to Azure OpenAI and Azure AI Search.
- First agent or prompt-flow style workflow built in AI Foundry.
- Retrieval integrated into the Foundry workflow.
- Evaluation and trace surfaces in AI Foundry enabled.

## What this day proves
- You can implement an end-to-end Agentic RAG workflow with AI Foundry as the primary control plane.
- You understand the managed path before building the custom path.

## 6-Hour Plan
1. Create or configure the AI Foundry workflow or agent surface.
2. Connect shared retrieval assets from Day 3.
3. Implement prompt or tool configuration for question answering with citations.
4. Run test conversations and save traces or runs inside AI Foundry.
5. Enable AI Foundry evaluation or experiment tracking.
6. Document where AI Foundry accelerates delivery and where it constrains control.

## Exit Criteria
- Working AI Foundry-based RAG workflow returns grounded answers.
- Foundry project has connected model and retrieval resources.
- Initial managed-workflow pros and cons are documented.

## Suggested Commit
feat(day-4): build Azure AI Foundry end-to-end agentic workflow

## LinkedIn Prompt
Best practice #4 for Agentic RAG on Azure: start with the managed path first. Azure AI Foundry gives you the fastest path to a working end-to-end workflow and helps clarify which parts you should keep managed versus custom-build later.

## Shipped (Day 4 — 2026-04-17)
- `src/foundry/rag_agent.py` — `FoundryRagAgent` using azure-ai-agents SDK with managed thread lifecycle
- `src/foundry/response.py` — `FoundryResponse` dataclass (content, citations, run_id)
- `src/foundry/evaluation.py` — `evaluate_response` with citation detection and relevance scoring
- `src/foundry/__init__.py` — public surface
- `tests/foundry/` — unit tests (all passing)
- Commit: `feat(day-4)` — CI green, 64 tests passing

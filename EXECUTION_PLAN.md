# Enterprise Agentic RAG on Azure — 10-Day Execution Plan

Start date: 2026-04-16  
Target effort: 6 hours/day (60 hours total)  
Target audience: Solution Architect / Azure Cloud Architect / AI Architect

## Daily Operating Rules
- Work exactly 6 focused hours per day.
- Commit to GitHub every day with meaningful messages.
- Keep CI green before ending each day.
- Publish one LinkedIn post daily (build-in-public).
- Write architecture decisions as ADR notes.

## Architecture Tracks

### Track A — Azure AI Foundry End-to-End
- **Primary platform**: Azure AI Foundry project
- **LLM and embeddings**: Azure OpenAI deployments via AI Foundry
- **Workflow surface**: AI Foundry agent or Prompt Flow style orchestration
- **Retrieval**: Azure AI Search connected through AI Foundry
- **Evaluation**: AI Foundry evaluations and prompt/runtime experiments
- **Safety**: AI Foundry governance plus Azure AI Content Safety

### Track B — Azure-Based Custom Architecture
- **LLM**: Azure OpenAI (GPT-4o)
- **Agent Framework**: LangGraph (ReAct loop, multi-agent)
- **Vector Store**: Azure AI Search (hybrid: keyword + vector + semantic reranker)
- **Document Parsing**: Azure Document Intelligence
- **Memory**: Redis Cache (short-term) + Azure AI Search (long-term)
- **Safety**: Azure AI Content Safety + custom guardrails
- **Observability**: OpenTelemetry + Azure Application Insights
- **Deployment**: Azure Container Apps + Azure API Management
- **Secrets**: Azure Key Vault + Managed Identity (zero secrets in code)

## Day-by-Day Plan
1. Day 1: Repository setup, CI/CD pipeline, guardrails and circuit breaker. ✅
2. Day 2: Azure foundation for both tracks — AI Foundry project, Azure OpenAI, AI Search, Key Vault, Managed Identity, cost model. ✅
3. Day 3: Shared ingestion and retrieval foundation — Document Intelligence, chunking, embeddings, AI Search indexing. ✅
4. Day 4: Azure AI Foundry end-to-end RAG + agent workflow — project connections, agent flow, evaluation hooks. ✅
5. Day 5: Azure-based custom agent workflow — LangGraph ReAct loop, tool-calling, citations, side-by-side track comparison. ✅
6. Day 6: Evaluation gate and quality thresholds — citation rate and relevance gate in CI, threshold-driven failure. ✅
7. Day 7: OpenTelemetry tracing + Azure AI Content Safety — structured spans on both tracks, input safety guardrail. ✅
8. Day 8: Multi-agent planner pattern — planner agent routing to specialist agents, state handoff, tradeoff documentation. ✅
9. Day 9: Azure Container Apps + Azure API Management deployment — containerize custom runtime, APIM gateway, managed identity at runtime. ✅
10. Day 10: Full architecture refresh — when to use what, tradeoffs, performance, memory, cost, security, orchestration, and agent-pattern guidance. ✅

## Status Snapshot (2026-04-20)
- Plan completion: 10/10 days complete.
- Quality gate status: ruff, mypy, pytest, and bandit passing.
- Documentation status: tracker, ADRs, TODO, and rebuild runbook are committed and pushed.
- Remaining work: optional operational evidence capture (post-deploy smoke run URL/screenshots).

## Daily File Map
- Master checklist: DAILY_CHECKLIST.md
- Progress tracker: .github/EXECUTION_TRACKER.md
- ADRs: docs/ARCHITECTURE_DECISIONS.md
- Day guides: docs/DAY_1.md ... docs/DAY_10.md

## Daily Start Routine (10 minutes)
1. Open DAILY_CHECKLIST.md.
2. Open today guide in docs/DAY_X.md.
3. Confirm yesterday CI is green.
4. Define top 3 outcomes for the day.

## Daily End Routine (20 minutes)
1. Run tests and quality checks.
2. Push final commit for the day.
3. Update DAILY_CHECKLIST.md and EXECUTION_TRACKER.md.
4. Publish LinkedIn post draft.

## Success Criteria by Day 10
- Working understanding and implementation path for both Azure AI Foundry end-to-end Agentic RAG and Azure-based custom Agentic RAG.
- Azure AI Foundry project with agent workflow, model connections, and evaluation surface.
- LangGraph-based custom agent with Azure OpenAI tool-calling and Azure AI Search retrieval.
- Shared ingestion, memory, safety, and observability patterns documented for both tracks.
- Comparison framework for performance, memory, cost, security, orchestration patterns, deployment choices, and agent patterns.
- Final Day 10 refresh that clearly answers when to use each approach and why.

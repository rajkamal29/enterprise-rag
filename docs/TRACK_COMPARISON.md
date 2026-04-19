# Orchestration Track Comparison: Azure AI Foundry vs LangGraph

**Audience:** Solution Architects, Technical Leads  
**Context:** This document compares the two agentic RAG tracks built in this portfolio project. Both tracks share the same ingestion pipeline, Azure AI Search index, Azure OpenAI models, and Managed Identity security posture. They differ in how the agent orchestration layer is built and operated.

---

## 1. Architecture Overview

### Track A — Azure AI Foundry (Managed)

```
Client
  │
  ▼
FoundryRagAgent.ask()
  │  creates Thread + Run via AgentsClient SDK
  ▼
Azure AI Foundry (control plane)
  │  schedules tool calls on your behalf
  ├──► AzureAISearchTool ──► rag-index (Azure AI Search)
  │
  ▼
GPT-4o (Azure OpenAI)
  │  synthesises answer with citations
  ▼
AgentResponse { content, citations, run_id, thread_id }
```

### Track B — LangGraph ReAct (Custom)

```
Client
  │
  ▼
LangGraphRagAgent.ask()
  │  runs a StateGraph compiled in your Python process
  ▼
LangGraph ReAct loop (your code, your machine/container)
  │
  ├── llm node ──► AzureChatOpenAI (gpt-4o) with tool-binding
  │
  └── tools node ──► search_tool() ──► SearchClient ──► rag-index
          │
          └── returns formatted chunks + sources
  │
  ▼
AgentResponse { content, citations, request_id, tool_call_ids }
```

---

## 2. Feature Comparison

| Dimension | Track A: AI Foundry | Track B: LangGraph |
|---|---|---|
| **Orchestration host** | Azure cloud (managed service) | Your Python process (ACA / VM) |
| **State management** | Thread + Run objects in Foundry | Explicit `TypedDict` in your code |
| **Retrieval coupling** | `AzureAISearchTool` (SDK abstraction) | `SearchClient` direct call (full control) |
| **Tool definition** | Foundry tool schema (JSON config) | Python `@tool` decorated function |
| **Query type** | SIMPLE / SEMANTIC (no integrated vectorizer needed) | BM25, vector, or hybrid — your choice |
| **Tracing** | Foundry portal (Run ID, thread timeline) | OpenTelemetry spans → Azure Application Insights |
| **Evaluation** | Foundry Evaluation UI + metrics | RAGAS / custom CI gate |
| **Unit testability** | Hard — requires live Foundry endpoint | Easy — mock the tool function |
| **Conversation memory** | Thread persists in Foundry | You manage message list in state |
| **Multi-agent routing** | Limited — single agent per run | Full graph branching (planner → specialist) |
| **Streaming** | Not supported in AgentsClient v1 | Supported via LangChain `astream_events` |
| **Cold start** | Agent creation on first call (~2s) | Graph compilation at startup (~0.1s) |
| **Vendor lock-in** | Azure AI Foundry API surface | LangChain/LangGraph OSS (portable) |
| **Operational overhead** | Low — Microsoft manages the runtime | Higher — you own the container + scaling |

---

## 3. When to Choose Track A (AI Foundry)

Use AI Foundry when:

- **Speed to value is the primary constraint.** Foundry removes infrastructure decisions — you get a working agent in hours, not days.
- **The team is small and ops capacity is limited.** No container orchestration, no trace pipeline, no scaling policy to maintain.
- **Governance and compliance are central.** Foundry integrates with Azure Policy, Responsible AI dashboard, and Content Safety natively.
- **You need the evaluation UI.** Foundry's experiment tracking and prompt comparison surfaces are significantly faster than building your own.
- **The retrieval pattern is well-understood and stable.** If you know BM25 + semantic reranker is sufficient, the `AzureAISearchTool` abstraction is appropriate.

**Typical client profile:** Enterprise team starting their first production RAG system. ISV building on top of Azure. Regulated industry (financial services, healthcare) needing audit trails managed by Microsoft.

---

## 4. When to Choose Track B (LangGraph)

Use LangGraph when:

- **Multi-step reasoning or conditional routing is required.** ReAct loops, planner-to-specialist handoffs, and retry-on-failure logic require explicit graph edges — not possible inside a single Foundry agent.
- **You need to unit-test agent behaviour without live Azure services.** LangGraph nodes are Python functions; tools can be mocked. CI runs in seconds.
- **Retrieval strategy needs to vary at runtime.** Different tools for different query types, fallback to a secondary index, or cross-index federation all require programmatic control.
- **Streaming responses to the UI are required.** LangGraph supports token-by-token streaming; Foundry AgentsClient v1 does not.
- **You are building a platform, not a single agent.** LangGraph composes naturally into multi-agent systems (Day 8 planner pattern) and is portable across Azure, AWS, and on-premises.
- **Observability depth matters.** Every node becomes an OpenTelemetry span. You own the trace schema and can correlate agent behaviour with business metrics.

**Typical client profile:** Platform engineering team building a reusable agent runtime. Product team that needs streaming chat UI. Advanced enterprise with complex multi-document, multi-step query patterns.

---

## 5. Cost Model

| Cost driver | Track A | Track B |
|---|---|---|
| LLM tokens | Pay-per-token (same model) | Pay-per-token (same model) |
| Azure AI Search queries | Same index, same query cost | Same index, same query cost |
| Compute | None — Foundry managed | ACA: ~$0.02–$0.10/hour depending on SKU |
| Foundry overhead | Included in Azure subscription | None |
| Observability | Foundry portal (included) | App Insights ingestion (~$2.30/GB) |

**Net difference:** Track B adds a small compute and observability cost but removes Foundry API dependency cost for high-volume workloads. At enterprise scale (>10M tokens/day), the compute cost of Track B is negligible vs token cost.

---

## 6. Migration Path

These tracks are not mutually exclusive. The recommended progression:

```
Day 4   Build Track A (Foundry) ──► Validate retrieval quality + citation behaviour
         │
Day 5   Build Track B (LangGraph) ──► Validate same workload with explicit control
         │
Day 8   Extend Track B ──► Multi-agent planner (complex queries, parallel retrieval)
         │
Day 9   Deploy Track B ──► Azure Container Apps + APIM (production traffic)
         │
Day 10  Decide ──► Which track owns which query class in production
```

A mature enterprise deployment often runs **both tracks simultaneously**:
- Foundry for simple Q&A and content-moderated customer-facing queries
- LangGraph for complex research queries requiring multi-step reasoning

---

## 7. Decision Guidance Summary

> **If you are starting a new project:** Start with Track A. Get something working and evaluated before adding orchestration complexity.
>
> **If you need multi-step reasoning, streaming, or testability:** Track B is necessary. LangGraph's explicit state model pays for itself within one sprint.
>
> **If you are designing a platform for multiple teams:** Track B. The composability and portability of LangGraph across Azure services and future model providers justifies the additional engineering.
>
> **If you need both:** Build Track A first, validate retrieval quality, then build Track B against the same index and system prompt. The shared `AgentResponse` dataclass and `evaluate_response()` function allow direct A/B comparison on the same questions.

---

## 8. Related Decisions

- [ADR-3: Dual-Track Delivery](ARCHITECTURE_DECISIONS.md#adr-3-dual-track-delivery)
- [ADR-5: LangGraph for the Custom Orchestration Path](ARCHITECTURE_DECISIONS.md#adr-5-langgraph-for-the-custom-orchestration-path)
- [ADR-7: Dual Evaluation Strategy](ARCHITECTURE_DECISIONS.md#adr-7-dual-evaluation-strategy)
- [ADR-14: Explicit Ingestion Pipeline](ARCHITECTURE_DECISIONS.md#adr-14-explicit-ingestion-pipeline-over-azure-ai-search-integrated-vectorization)

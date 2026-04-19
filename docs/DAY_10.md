# Day 10 - Architecture Refresh + Tradeoff Compendium

Goal: Refresh every major topic covered in the build and produce a clear when-to-use-what guide for both tracks.

## Outcomes
- Final side-by-side comparison: Azure AI Foundry end-to-end vs Azure-based custom Agentic RAG.
- Topic refresh for performance, memory, cost optimization, security, orchestration, retrieval, observability, deployment, and agent patterns.
- Recommendation matrix for prototype, enterprise pilot, and production.
- SA/AI Architect-level Q&A bank with topic-by-topic tradeoffs.
- Final architecture narrative and portfolio packaging.

## Required comparison topics
| Topic | Questions to answer |
|---|---|
| Orchestration | When is AI Foundry enough, and when do you need LangGraph? |
| Agent patterns | Single agent vs planner-router vs multi-agent specialists |
| Memory | Session window vs persistent memory vs retrieval context |
| Performance | What optimizations matter first at low, medium, and high scale? |
| Cost optimization | Token budgets, caching, top-k tuning, model selection, runtime choice |
| Security | Identity, network isolation, safety controls, auditability |
| Observability | AI Foundry run surfaces vs OpenTelemetry and App Insights |
| Deployment | Managed workflow surface vs custom runtime on ACA/APIM |
| Retrieval | Keyword, vector, hybrid, reranking, metadata filtering |

## 6-Hour Plan
1. Build side-by-side comparison tables for every major topic.
2. Write explicit when-to-use-what guidance for Track A and Track B.
3. Create prototype, pilot, and production recommendation matrix.
4. Prepare architect Q&A answers using the comparison evidence from Days 2-9.
5. Polish README and navigation so the dual-track story is obvious.
6. Publish wrap-up post summarizing both approaches and the final recommendations.

## Exit Criteria
- Every major topic has a tradeoff summary and recommendation.
- A reader can identify when to choose AI Foundry, when to choose custom Azure architecture, and when to combine them.
- Repo is interview-ready for architecture discussions, not just implementation demos.

## Suggested Commit
docs(day-10): add full architecture refresh and tradeoff compendium

## LinkedIn Prompt
Wrapped up a dual-track Agentic RAG build on Azure: one path using Azure AI Foundry end-to-end and one path using custom Azure architecture with LangGraph. The final result is not just code, but clear guidance on when to use which approach across orchestration, memory, performance, cost, security, and deployment.

## Day 10 Results (Completed)

### Final recommendation by scenario
| Scenario | Preferred approach | Why |
|---|---|---|
| Rapid prototype (days to weeks) | Track A (Azure AI Foundry) | Fastest setup, managed orchestration/evaluation surface, lowest platform overhead |
| Enterprise pilot (weeks to few months) | Hybrid (Track A + selected custom components) | Keep speed of managed workflow while introducing custom retrieval and observability where needed |
| Production with strict control and advanced routing | Track B (Custom Azure + LangGraph) | Full control of orchestration, deployment, telemetry, security boundaries, and multi-agent behavior |

### When to use what
| Topic | Choose Track A when... | Choose Track B when... |
|---|---|---|
| Orchestration | Linear or moderately branching flow is enough | Planner-router patterns, custom state transitions, or specialist agents are required |
| Retrieval | Standard managed retrieval quality is acceptable | You need explicit chunking/indexing strategy, hybrid tuning, and metadata-driven retrieval logic |
| Memory | Session-level context is sufficient | You need custom short-term/long-term memory policies and store selection |
| Performance | Managed defaults satisfy latency targets | You must tune cold-start behavior, scaling policy, top-k/rerank policy, and per-step execution path |
| Cost | Team prefers lower engineering overhead | Team can trade engineering effort for lower token/runtime costs via tighter controls |
| Security | Managed controls satisfy compliance baseline | You need strict least-privilege RBAC, custom policy gates, and explicit network/runtime boundaries |
| Observability | High-level run tracing is sufficient | You need low-level OpenTelemetry spans, cross-service correlation, and custom SLO instrumentation |
| Deployment | Managed surface is preferred | You require containerized runtime behind APIM with explicit release controls |

### Architecture decision summary
1. Use Track A to maximize delivery speed for early-stage product validation.
2. Move to Track B when enterprise requirements demand stronger control over routing, telemetry, and deployment topology.
3. Use a hybrid pattern for transition phases instead of a hard cut-over.
4. Keep shared ingestion, safety, and evaluation standards across both tracks to preserve comparability.

### NFR targets (production baseline)
| Dimension | Target | Notes |
|---|---|---|
| Availability | 99.9% monthly | Requires tested rollback and incident runbook |
| Health latency | p95 <= 300 ms | Measured at APIM edge |
| Ask latency | p95 <= 12 s | Workload-specific; tune top-k, model, and prompts |
| Error budget | <= 0.1% 5xx rate | Enforced through alerts and release gates |
| Recovery time (RTO) | <= 4 hours | Includes infra + identity recovery |
| Data loss (RPO) | <= 15 minutes | Requires backup/restore and index refresh strategy |
| Security | Zero hardcoded secrets | Managed identity and Key Vault only |

### DR and deployment options
| Option | Strengths | Tradeoffs | Recommended use |
|---|---|---|---|
| Single-region with runbook failover | Lowest cost and simplest ops | Higher regional outage risk | Early production with moderate criticality |
| Active-passive dual region | Better resilience and controlled failover | Higher cost and operational complexity | Enterprise workloads with stricter uptime |
| Active-active dual region | Highest availability and traffic resilience | Most complex data consistency and routing model | Mission-critical, high-scale workloads |

Decision for current project phase:
1. Baseline on single-region with hardened runbooks and smoke checks.
2. Move to active-passive once uptime target or compliance requirements exceed single-region tolerance.

### Interview/architect talking points
1. Why dual track: delivery speed and enterprise control optimize different constraints.
2. Why Day 9 deployment matters: custom runtime viability is proven only after identity, APIM, and smoke tests pass.
3. Why evaluation gates matter: CI-enforced relevance/citation thresholds prevent silent quality regression.
4. Why observability matters: shared span schema enables apples-to-apples diagnostics across both approaches.

### Exit check
- Tradeoff matrix complete across orchestration, retrieval, memory, performance, cost, security, observability, and deployment.
- Recommendation matrix complete for prototype, pilot, and production.
- Guidance now answers when to use Track A, Track B, or hybrid.

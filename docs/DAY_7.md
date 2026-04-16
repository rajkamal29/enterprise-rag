# Day 7 - Observability and Responsible AI

Goal: Make every agent step traceable and enforce responsible AI policies.

## Outcomes
- OpenTelemetry traces span the full agent reasoning loop (every node, every tool call).
- Azure Application Insights receives traces, metrics, and exceptions.
- Azure AI Content Safety screens inputs and outputs.
- Groundedness enforcement: agent answer rejected if not supported by retrieved context.
- Citation enforcement: every answer must reference source documents.

## Observability Stack
```
Agent Step (LangGraph node)
    │
    ▼  OpenTelemetry span
Azure Application Insights
    │
    ▼  Kusto queries
Azure Monitor Dashboard
    │
    ▼  Alert rules
Alert → PagerDuty / Teams
```

## Responsible AI Layers
| Layer | Implementation | Purpose |
|---|---|---|
| Input filter | Azure AI Content Safety | Block harmful prompts |
| Output filter | Azure AI Content Safety | Block harmful completions |
| Groundedness | Custom scorer vs. retrieved context | Prevent hallucination |
| Citation | Enforce source references in answer | Auditability |
| Audit log | Immutable log of every query + answer | Compliance |

## 6-Hour Plan
1. Add OpenTelemetry SDK, instrument every LangGraph node with spans.
2. Configure Azure Application Insights exporter.
3. Integrate Azure AI Content Safety for input screening.
4. Implement groundedness scorer: compare answer to context, flag if below threshold.
5. Implement citation enforcer: parse answer for source references, reject if missing.
6. Test: inject a hallucinated answer, confirm it is blocked.

## Exit Criteria
- Full agent trace visible in Application Insights end-to-end.
- Hallucinated answer (not grounded in context) is blocked by groundedness check.
- Harmful input is blocked by Azure AI Content Safety.

## Suggested Commit
feat(day-7): OpenTelemetry tracing and Responsible AI enforcement

## LinkedIn Prompt
Best practice #7 for Enterprise Agentic RAG on Azure: Responsible AI is not a checkbox — it is a pipeline stage. Azure AI Content Safety on inputs AND outputs. Groundedness scoring before the answer leaves the system. Citation enforcement for auditability. All of this must be in the critical path, not an afterthought.

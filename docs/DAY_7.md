# Day 7 - OpenTelemetry Tracing + Azure AI Content Safety

Goal: Add structured observability to both tracks and enforce a content safety guardrail on all agent inputs.

## Outcomes
- OpenTelemetry spans on every `ask()` call in Track A and Track B.
- Azure Application Insights as the OTel exporter.
- Azure AI Content Safety guardrail blocks unsafe inputs before they reach the agent.
- Both tracks emit the same span schema for fair latency comparison.

## Why this day matters
- You cannot tune what you cannot measure.
- Responsible AI controls should be enforced at the infrastructure layer, not left to individual callers.
- A shared OTel schema on both tracks enables apples-to-apples latency comparison in Day 10.

## 6-Hour Plan
1. Add `src/observability/tracing.py` — OTel tracer factory pointing to Azure Application Insights.
2. Instrument `FoundryRagAgent.ask()` (Track A) with a root span and child spans for retrieval + generation.
3. Instrument `LangGraphRagAgent.ask()` (Track B) with equivalent spans.
4. Add `src/guardrails/content_safety.py` — `ContentSafetyGuardrail` wrapping Azure AI Content Safety.
5. Wire the guardrail as a pre-check in both agents.
6. Add unit tests for tracing helpers and the content safety guardrail.

## Files to create
| File | Purpose |
|---|---|
| `src/observability/__init__.py` | Package marker |
| `src/observability/tracing.py` | `get_tracer()` factory, span helpers |
| `src/guardrails/content_safety.py` | `ContentSafetyGuardrail.check(text)` |
| `tests/observability/test_tracing.py` | Unit tests for span helpers |
| `tests/guardrails/test_content_safety.py` | Unit tests for guardrail |

## Span schema (both tracks)
| Span name | Attributes |
|---|---|
| `rag.ask` | `track`, `question_length`, `run_id` |
| `rag.retrieve` | `track`, `query`, `result_count` |
| `rag.generate` | `track`, `model`, `token_count` |

## Exit Criteria
- Both tracks emit OTel spans visible in Application Insights (or verified via in-process exporter in tests).
- Content safety guardrail raises `ValueError` on blocked content.
- All tests pass, ruff/mypy/bandit clean.

## Suggested Commit
feat(day-7): add OpenTelemetry tracing and Azure AI Content Safety guardrail

## LinkedIn Prompt
Best practice #7 for Agentic RAG on Azure: instrument before you optimize. Adding OpenTelemetry spans to both your managed and custom agent paths gives you the evidence you need to make architecture decisions with confidence — and Azure AI Content Safety keeps the guardrails where they belong: at the infrastructure layer.

# Day 5 - Tracing, Metrics, and Alerts

Goal: Make the RAG system observable and debuggable in production.

## Outcomes
- End-to-end request tracing.
- Alert thresholds for latency and error spikes.
- Dashboard-ready metric schema.

## 6-Hour Plan
1. Add trace IDs through pipeline stages.
2. Capture stage latency and failure labels.
3. Add alert rules for SLO breaches.
4. Validate with failure simulation.
5. Document runbook basics.
6. Push and verify CI.

## Exit Criteria
- Root-cause path visible for failed requests.
- Alert conditions tested.

## Suggested Commit
feat(day-5): implement tracing and operational alerts

## LinkedIn Prompt
Instrumented RAG with trace-driven debugging and SLO alerts.

# Day 6 - Fallback and Graceful Degradation

Goal: Preserve service quality when dependencies fail.

## Outcomes
- Fallback cascade strategy.
- Safe responses when context quality is low.
- Retry/backoff and circuit handling policy.

## 6-Hour Plan
1. Define fallback levels and trigger rules.
2. Implement fallback orchestrator.
3. Add low-confidence response handling.
4. Simulate dependency failures.
5. Test latency and correctness under fallback.
6. Push with test evidence.

## Exit Criteria
- Service responds safely during partial outages.
- Fallback path timing stays within target limits.

## Suggested Commit
feat(day-6): add fallback cascade and graceful degradation

## LinkedIn Prompt
Designed failure-first RAG with deterministic fallback levels.

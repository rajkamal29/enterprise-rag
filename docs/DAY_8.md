# Day 8 - Security, Observability, and Orchestration Patterns

Goal: Secure both tracks, make them observable, and compare orchestration and agent patterns.

## Outcomes
- Responsible AI controls documented and applied across both tracks.
- OpenTelemetry and Azure Monitor tracing applied to the custom path, with Foundry trace surfaces captured for the managed path.
- Single-agent, planner-agent, and multi-agent patterns compared.
- Security and orchestration tradeoffs prepared for Day 10 review.

## Topics to cover
| Topic | Comparison |
|---|---|
| Security | Key Vault, Managed Identity, AI Content Safety, network boundaries |
| Observability | AI Foundry run surfaces vs OpenTelemetry + App Insights |
| Orchestration | Managed workflow vs LangGraph state graph |
| Agent patterns | Single agent vs planner-router vs multi-agent specialists |

## 6-Hour Plan
1. Add safety and groundedness controls to both tracks.
2. Instrument custom workflow with OpenTelemetry and App Insights.
3. Capture equivalent observability artifacts from AI Foundry.
4. Benchmark single-agent, planner, and multi-agent patterns on the same workload.
5. Document where managed orchestration is sufficient and where custom routing wins.
6. Prepare security and orchestration comparison matrices for Day 10.

## Exit Criteria
- Security controls exist for both tracks.
- Observability differences are documented with evidence.
- Agent-pattern guidance exists for at least three query archetypes.

## Suggested Commit
feat(day-8): add security, observability, and orchestration pattern comparisons

## LinkedIn Prompt
Best practice #8 for Agentic RAG on Azure: not every workload needs multi-agent orchestration. Choose the simplest agent pattern that meets the reasoning need, then add observability before adding complexity.

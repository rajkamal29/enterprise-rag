# Day 9 - Runtime and Deployment Patterns

Goal: Cover the runtime and deployment story for both the AI Foundry-managed path and the custom Azure app path.

## Outcomes
- AI Foundry runtime path documented and tested for managed workflow execution.
- Custom runtime deployed through Azure Container Apps and API Management.
- Network, identity, and deployment tradeoffs documented for both tracks.
- Clear recommendation matrix for prototype, enterprise pilot, and production scale.

## Track comparison
| Track | Runtime focus |
|---|---|
| Track A | AI Foundry project and managed workflow surface |
| Track B | FastAPI or app runtime on ACA/APIM with private networking |

## 6-Hour Plan
1. Document the execution model for AI Foundry-managed workflows.
2. Build or polish the custom runtime for LangGraph-based access.
3. Add ACA, APIM, and networking guidance for Track B.
4. Compare deployment complexity, flexibility, cost, and control.
5. Define when to start in Track A and when to move to Track B.
6. Save deployment recommendation matrix for Day 10 refresh.

## Exit Criteria
- Both runtime paths are described with security and ops implications.
- Deployment decision criteria are documented.
- Recommendation matrix exists for prototype, pilot, and production.

## Suggested Commit
feat(day-9): document runtime and deployment patterns for both tracks

## LinkedIn Prompt
Best practice #9 for Agentic RAG on Azure: separate workflow design from runtime design. AI Foundry may be the right workflow control plane while Azure Container Apps may be the right runtime for the custom path.

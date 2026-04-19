# Day 9 - Azure Container Apps + Azure API Management Deployment

Goal: Package the custom LangGraph agent as a containerised API and deploy it behind Azure API Management with Managed Identity.

## Outcomes
- `LangGraphRagAgent` exposed as a FastAPI endpoint.
- Docker image built and pushed to Azure Container Registry.
- Azure Container App deployed with Managed Identity (no secrets in environment).
- Azure API Management gateway in front of the Container App.
- Network and identity tradeoffs documented vs AI Foundry managed path.

## Track comparison
| Track | Runtime |
|---|---|
| Track A | Azure AI Foundry managed project runtime |
| Track B | FastAPI on ACA, APIM gateway, private networking |

## 6-Hour Plan
1. Add `src/api/app.py` — FastAPI app with `/ask` endpoint wrapping `LangGraphRagAgent`.
2. Write `Dockerfile` — multi-stage, non-root user, uv-based install.
3. Add `infra/aca.bicep` — Container App + Container Registry + APIM.
4. Deploy to Azure and verify end-to-end request via APIM URL.
5. Verify Managed Identity is the only credential (no connection strings in env).
6. Document deployment complexity, runtime cost, and when ACA/APIM is justified vs AI Foundry.

## Files to create
| File | Purpose |
|---|---|
| `src/api/__init__.py` | Package marker |
| `src/api/app.py` | FastAPI `/ask` endpoint |
| `Dockerfile` | Production container image |
| `infra/aca.bicep` | ACA + ACR + APIM Bicep module |
| `tests/api/test_app.py` | FastAPI TestClient unit tests |

## Exit Criteria
- Container starts locally and responds to `/ask` requests.
- Bicep module deploys ACA, ACR, and APIM without errors.
- All tests pass, ruff/mypy/bandit clean.

## Suggested Commit
feat(day-9): add FastAPI runtime and ACA/APIM deployment for Track B

## LinkedIn Prompt
Best practice #9 for Agentic RAG on Azure: separate the agent runtime from the agent logic. Packaging LangGraph inside a FastAPI container lets you deploy behind Azure API Management with rate limiting, auth, and monitoring — while the agent code stays clean.

# Day 9 - Deployment: Azure Container Apps + APIM + Private Networking

Goal: Deploy the Agentic RAG system to Azure with production-grade security and scalability.

## Outcomes
- Multi-stage Dockerfile (non-root user, minimal base image, no secrets baked in).
- Deployed to Azure Container Apps with KEDA autoscaling.
- Azure API Management as the secure front door (auth, rate limiting, versioning).
- Private Endpoints for all backend services (AI Search, OpenAI, Key Vault, Cosmos).
- GitHub Actions CD pipeline: build → push to ACR → deploy to ACA.

## Deployment Architecture
```
Client
  │
  ▼
Azure API Management  ← Auth (AAD), Rate limiting, Versioning
  │
  ▼  (private VNET)
Azure Container Apps  ← KEDA autoscale, Managed Identity
  │
  ├── Azure OpenAI          (Private Endpoint)
  ├── Azure AI Search        (Private Endpoint)
  ├── Azure Key Vault        (Private Endpoint)
  └── Azure Cosmos DB        (Private Endpoint)
```

## Dockerfile Best Practices
```dockerfile
# Multi-stage: builder stage + minimal runtime stage
FROM python:3.12-slim AS builder
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN pip install uv && uv sync --frozen --no-dev

FROM python:3.12-slim
WORKDIR /app
# Non-root user — never run as root in containers
RUN useradd --uid 1001 --no-create-home appuser
COPY --from=builder /app/.venv .venv
COPY src/ src/
USER appuser
ENV PATH="/app/.venv/bin:$PATH"
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## 6-Hour Plan
1. Write `Dockerfile` (multi-stage, non-root, no secrets).
2. Add `src/api/main.py` — FastAPI app wrapping the LangGraph agent.
3. Create Azure Container Registry, build and push image.
4. Deploy to Azure Container Apps with Managed Identity and KEDA scaling rules.
5. Configure Azure API Management with JWT validation and rate limiting policy.
6. Verify private endpoint connectivity; add CD workflow to GitHub Actions.

## Exit Criteria
- Container starts, health check passes, agent responds to a test query.
- All service calls go through Private Endpoints (no public internet access).
- CD pipeline deploys successfully on push to main.

## Suggested Commit
feat(day-9): Dockerfile, Azure Container Apps deployment, APIM, private networking

## LinkedIn Prompt
Best practice #9 for Enterprise Agentic RAG on Azure: Azure Container Apps is the right deployment target for most Agentic RAG workloads. Serverless K8s, KEDA scaling, built-in ingress, Managed Identity — and it costs nothing when idle. Pair it with Azure API Management for auth and rate limiting, and Private Endpoints to keep all traffic off the public internet.

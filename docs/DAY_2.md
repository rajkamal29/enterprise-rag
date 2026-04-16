# Day 2 - Azure Infrastructure Foundation

Goal: Provision all Azure services, wire secrets securely, establish cost model.

## Outcomes
- Azure OpenAI (GPT-4o) and Azure AI Search provisioned.
- Managed Identity configured — zero API keys in code.
- Azure Key Vault holds all service endpoints and credentials.
- Per-request cost model for tokens + AI Search compute units.

## Azure Services
| Service | Purpose |
|---|---|
| Azure OpenAI (GPT-4o) | LLM for generation and tool-calling |
| Azure OpenAI (text-embedding-3-large) | Embedding model |
| Azure AI Search | Hybrid retrieval (vector + keyword + semantic) |
| Azure Key Vault | Secret storage — no secrets in code |
| Azure Managed Identity | Service-to-service auth — no API keys |
| Azure App Configuration | Environment-specific settings |

## 6-Hour Plan
1. Provision Azure OpenAI and deploy GPT-4o + embedding model.
2. Provision Azure AI Search with semantic ranking enabled.
3. Create Azure Key Vault and store all connection strings.
4. Configure Managed Identity for local dev (DefaultAzureCredential).
5. Implement cost model: token pricing + AI Search CU pricing.
6. Add tests for cost model, push ADR for Managed Identity decision.

## Key Code
```python
# Always use DefaultAzureCredential — works locally and in ACA
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

credential = DefaultAzureCredential()
client = SecretClient(vault_url=os.environ["KEY_VAULT_URI"], credential=credential)
```

## Exit Criteria
- `DefaultAzureCredential` authenticates to Key Vault locally.
- Cost estimate function returns bounded result for test workload.
- No secrets in environment variables or code.

## Suggested Commit
feat(day-2): provision Azure foundation with Managed Identity and cost model

## LinkedIn Prompt
Best practice #2 for Enterprise Agentic RAG on Azure: Managed Identity everywhere. Zero secrets in code from day one. Use DefaultAzureCredential — it works locally, in CI, and in Azure Container Apps without changing a single line.

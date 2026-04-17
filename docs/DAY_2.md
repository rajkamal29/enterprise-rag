# Day 2 - Azure Foundation for Both Tracks

Goal: Provision the common Azure and AI Foundry foundation used by both implementation paths.

## Outcomes
- Azure AI Foundry project created and connected to Azure OpenAI.
- Azure OpenAI GPT and embedding deployments provisioned.
- Azure AI Search, Key Vault, and Managed Identity configured.
- Shared cost model created for tokens, search, and runtime.

## Common Services
| Service | Purpose |
|---|---|
| Azure AI Foundry Project | Control plane for Track A |
| Azure OpenAI | Model and embedding deployments |
| Azure AI Search | Shared retrieval layer |
| Azure Key Vault | Secret and endpoint storage |
| Managed Identity | Secretless service authentication |
| Azure App Configuration | Environment-specific settings |

## Track split
- Track A: AI Foundry project, connections, model deployments, evaluation workspace.
- Track B: App-centric Azure runtime using the same OpenAI, Search, Key Vault, and identity base.

## 6-Hour Plan
1. Create Azure AI Foundry project and verify project connections.
2. Provision Azure OpenAI GPT-4o and embedding deployment.
3. Provision Azure AI Search with semantic ranking enabled.
4. Configure Key Vault and Managed Identity for both local and cloud access.
5. Implement shared cost model for tokens, search, and runtime requests.
6. Document which services are shared across Track A and Track B.

## Exit Criteria
- AI Foundry project is usable for Track A.
- DefaultAzureCredential authenticates locally.
- Shared cost model produces bounded estimates.

## Suggested Commit
feat(day-2): provision Azure and AI Foundry foundation for both tracks

## LinkedIn Prompt
Best practice #2 for Agentic RAG on Azure: build one secure foundation for both AI Foundry workflows and custom app architectures. Shared identity, shared retrieval, shared cost model, no duplicate platform work.

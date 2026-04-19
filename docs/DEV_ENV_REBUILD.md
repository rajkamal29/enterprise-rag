# Rebuild Dev Environment After Deleting Azure Resource Group

This runbook recreates the development environment if `rg-erag-dev` is deleted.

## Scope

- Recreate shared Azure foundation (identity, Key Vault, OpenAI, AI Search, Foundry resources).
- Recreate runtime stack (ACR, ACA, APIM).
- Rebuild and push runtime image.
- Verify health and ask endpoints.

## Prerequisites

- Azure CLI installed and logged in (`az login`).
- Bicep available via Azure CLI (`az bicep install` if needed).
- `uv` installed for Python dependency and local verification commands.
- Correct subscription selected:

```powershell
az account set --subscription <SUBSCRIPTION_ID>
az account show --query "{name:name,id:id}" -o table
```

## 1. Recreate Resource Group

```powershell
az group create --name rg-erag-dev --location eastus --tags environment=dev project=enterprise-rag
```

## 2. Recreate Day 2 Foundation

Run the repository deployment script from project root:

```powershell
./infra/deploy.ps1 -Environment dev -Location eastus -ResourceGroup rg-erag-dev -ProjectPrefix erag2
```

Expected outcomes:
- Managed identity, Key Vault, Storage, OpenAI, AI Search, and Foundry resources are recreated.
- Local `.env` is refreshed with deployment outputs.

## 3. Recreate Day 9 Runtime Infra (ACR + ACA + APIM)

Deploy `infra/aca.bicep`:

```powershell
$openAiEndpoint = "https://oai-erag2-dev.openai.azure.com/"
$searchEndpoint = "https://srch-erag2-dev.search.windows.net"

az deployment group create \
  --resource-group rg-erag-dev \
  --name day9-aca-apim-rebuild \
  --template-file infra/aca.bicep \
  --parameters environment=dev projectPrefix=erag2 imageTag=day9 azureOpenAiEndpoint=$openAiEndpoint azureSearchEndpoint=$searchEndpoint
```

Note:
- This step creates ACR, ACA environment/app, and APIM.
- If image pull fails on first pass (image not yet pushed), continue with Step 4 and then redeploy this step once.

## 4. Build and Push Runtime Image to ACR

From project root:

```powershell
az acr build --registry acrerag2dev --image enterprise-rag-api:day9 --image enterprise-rag-api:latest .
```

If Step 3 had image pull issues, run Step 3 again after this build completes.

## 5. Verify Runtime Endpoint(s)

Get APIM gateway URL:

```powershell
$apimUrl = az apim show --resource-group rg-erag-dev --name apim-erag2-dev --query gatewayUrl -o tsv
$subKey = "<APIM_SUBSCRIPTION_KEY>"
```

Health check:

```powershell
Invoke-RestMethod -Method Get -Uri "$apimUrl/rag/health" -Headers @{"Ocp-Apim-Subscription-Key"=$subKey}
```

Ask check:

```powershell
$body = @{ question = "How do I deploy Azure OpenAI?" } | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri "$apimUrl/rag/ask" -ContentType "application/json" -Headers @{"Ocp-Apim-Subscription-Key"=$subKey} -Body $body
```

## 6. Local Quality Gate (Recommended)

```powershell
uv run ruff check .
uv run mypy src
uv run pytest
uv run bandit -r src
```

## 7. Post-Deploy Smoke Test (Recommended)

Trigger the GitHub Actions smoke workflow and store the run URL in tracker docs for evidence.

## Troubleshooting Quick Notes

- Deployment fails with provisioning errors:
  - Run `az deployment group show --resource-group rg-erag-dev --name <DEPLOYMENT_NAME> --query "properties.error" -o json`.
- ACA revision unhealthy or no response:
  - Check logs: `az containerapp logs show --resource-group rg-erag-dev --name aca-rag-erag2-dev --follow`.
- APIM returns unauthorized:
  - Confirm valid subscription key and that `subscriptionRequired` remains enabled in APIM config.
- Role assignment or identity timing issues:
  - Wait a few minutes and retry failed operation after RBAC propagation.

## Optional: Full Teardown Command

If you intentionally need to remove everything again:

```powershell
az group delete --name rg-erag-dev --yes --no-wait
```

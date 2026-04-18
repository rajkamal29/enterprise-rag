// Main Bicep template – Enterprise Agentic RAG on Azure
// Orchestrates all infra modules for Day 2 Azure foundation.
// Deploy via: infra/deploy.ps1 -Environment dev

targetScope = 'resourceGroup'

@description('Short environment name used as resource suffix (dev | staging | prod)')
@allowed(['dev', 'staging', 'prod'])
param environment string = 'dev'

@description('Azure region for all resources')
param location string = resourceGroup().location

@description('Short project prefix (max 8 chars) for naming resources')
@maxLength(8)
param projectPrefix string = 'erag'

@description('Object ID of the deployer (user/SP) for Key Vault Secrets Officer role')
param deployerPrincipalId string = ''

// ── Derived naming ───────────────────────────────────────────────────────────
var suffix = '${projectPrefix}-${environment}'
var identityName = 'mi-${suffix}'
var keyVaultName = 'kv-${suffix}'           // 3-24 chars
var storageAccountName = replace('st${suffix}', '-', '')  // no hyphens, lower
var openAiAccountName = 'oai-${suffix}'
var searchServiceName = 'srch-${suffix}'
var documentIntelligenceName = 'di-${suffix}'
var hubName = 'hub-${suffix}'
var projectName = 'proj-${suffix}'

var tags = {
  environment: environment
  project: 'enterprise-rag'
  managedBy: 'bicep'
}

// ── Managed Identity ─────────────────────────────────────────────────────────
module identity 'modules/managed-identity.bicep' = {
  name: 'identity'
  params: {
    location: location
    identityName: identityName
    tags: tags
  }
}

// ── Key Vault ────────────────────────────────────────────────────────────────
module keyVault 'modules/keyvault.bicep' = {
  name: 'keyvault'
  params: {
    location: location
    keyVaultName: keyVaultName
    managedIdentityPrincipalId: identity.outputs.principalId
    deployerPrincipalId: deployerPrincipalId
    tags: tags
  }
}

// ── Storage (AI Foundry Hub dependency) ──────────────────────────────────────
module storage 'modules/storage.bicep' = {
  name: 'storage'
  params: {
    location: location
    storageAccountName: storageAccountName
    managedIdentityPrincipalId: identity.outputs.principalId
    tags: tags
  }
}

// ── Azure OpenAI ─────────────────────────────────────────────────────────────
module openAi 'modules/openai.bicep' = {
  name: 'openai'
  params: {
    location: location
    openAiAccountName: openAiAccountName
    managedIdentityPrincipalId: identity.outputs.principalId
    tags: tags
  }
}

// ── Azure AI Search ──────────────────────────────────────────────────────────
module search 'modules/search.bicep' = {
  name: 'search'
  params: {
    location: location
    searchServiceName: searchServiceName
    managedIdentityPrincipalId: identity.outputs.principalId
    tags: tags
  }
}

// ── Azure Document Intelligence (Day 3 Ingestion) ──────────────────────────────
module documentIntelligence 'modules/documentintelligence.bicep' = {
  name: 'documentintelligence'
  params: {
    location: location
    documentIntelligenceName: documentIntelligenceName
    managedIdentityPrincipalId: identity.outputs.principalId
    tags: tags
  }
}

// ── Azure AI Foundry (Hub + Project) ─────────────────────────────────────────
module aiFoundry 'modules/ai-foundry.bicep' = {
  name: 'aifoundry'
  params: {
    location: location
    hubName: hubName
    projectName: projectName
    storageAccountId: storage.outputs.storageAccountId
    keyVaultId: keyVault.outputs.keyVaultId
    openAiAccountId: openAi.outputs.openAiId
    searchServiceId: search.outputs.searchServiceId
    managedIdentityPrincipalId: identity.outputs.principalId
    managedIdentityId: identity.outputs.identityId
    tags: tags
  }
}

// ── Outputs ──────────────────────────────────────────────────────────────────
// Captured in GitHub Actions / local scripts to seed .env / Key Vault secrets.

output managedIdentityClientId string = identity.outputs.clientId
output keyVaultUri string = keyVault.outputs.keyVaultUri
output openAiEndpoint string = openAi.outputs.openAiEndpoint
output chatDeploymentName string = openAi.outputs.chatDeploymentName
output embeddingDeploymentName string = openAi.outputs.embeddingDeploymentName
output searchEndpoint string = search.outputs.searchServiceEndpoint
output documentIntelligenceEndpoint string = documentIntelligence.outputs.documentIntelligenceEndpoint
output aiFoundryProjectConnectionString string = aiFoundry.outputs.projectConnectionString

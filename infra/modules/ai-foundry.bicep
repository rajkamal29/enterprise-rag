// Azure AI Foundry module
// Creates an AI Foundry Hub (kind: Hub) and an AI Foundry Project (kind: Project).
// The Hub is the shared platform resource; the Project is the application workspace.
// Both require an existing storage account and key vault as dependencies.

@description('Azure region')
param location string

@description('AI Foundry Hub name')
param hubName string

@description('AI Foundry Project name')
param projectName string

@description('Resource ID of the storage account backing the Hub')
param storageAccountId string

@description('Resource ID of the Key Vault associated with the Hub')
param keyVaultId string

@description('Resource ID of the Azure OpenAI account to connect')
param openAiAccountId string

@description('Resource ID of the Azure AI Search service to connect')
param searchServiceId string

@description('Principal ID of the user-assigned managed identity')
param managedIdentityPrincipalId string

@description('Resource ID of the user-assigned managed identity')
param managedIdentityId string

@description('Tags to apply to all resources')
param tags object = {}

// Built-in role: Azure Machine Learning Workspace Connection Secrets Reader
var amlSecretsReaderRoleId = 'ea01e6af-a1c1-4350-9563-ad00f8c72ec5'

// ── Hub ──────────────────────────────────────────────────────────────────────
resource hub 'Microsoft.MachineLearningServices/workspaces@2024-07-01-preview' = {
  name: hubName
  location: location
  tags: tags
  kind: 'Hub'
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${managedIdentityId}': {}
    }
  }
  properties: {
    friendlyName: hubName
    description: 'Enterprise Agentic RAG Hub'
    storageAccount: storageAccountId
    keyVault: keyVaultId
    publicNetworkAccess: 'Enabled'
    primaryUserAssignedIdentity: managedIdentityId
  }
}

// ── OpenAI connection on the Hub ─────────────────────────────────────────────
resource openAiConnection 'Microsoft.MachineLearningServices/workspaces/connections@2024-07-01-preview' = {
  parent: hub
  name: 'azure-openai'
  properties: {
    category: 'AzureOpenAI'
    authType: 'ProjectManagedIdentity'
    target: openAiAccountId
    credentials: {}
    metadata: {
      ResourceId: openAiAccountId
      ApiType: 'Azure'
    }
  }
}

// ── AI Search connection on the Hub ──────────────────────────────────────────
resource searchConnection 'Microsoft.MachineLearningServices/workspaces/connections@2024-07-01-preview' = {
  parent: hub
  name: 'azure-ai-search'
  properties: {
    category: 'CognitiveSearch'
    authType: 'ProjectManagedIdentity'
    target: searchServiceId
    credentials: {}
    metadata: {
      ResourceId: searchServiceId
      ApiType: 'Azure'
    }
  }
}

// ── Project (application workspace) ─────────────────────────────────────────
resource project 'Microsoft.MachineLearningServices/workspaces@2024-07-01-preview' = {
  name: projectName
  location: location
  tags: tags
  kind: 'Project'
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    friendlyName: projectName
    hubResourceId: hub.id
  }
}

// Grant managed identity secrets reader on the Hub
resource miSecretsReader 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(hub.id, managedIdentityPrincipalId, amlSecretsReaderRoleId)
  scope: hub
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', amlSecretsReaderRoleId)
    principalId: managedIdentityPrincipalId
    principalType: 'ServicePrincipal'
  }
}

output hubId string = hub.id
output hubName string = hub.name
output projectId string = project.id
output projectName string = project.name
// Connection string format: <region>.<subscription>.<resource_group>.<project_name>
output projectConnectionString string = '${location}.api.azureml.ms;${subscription().subscriptionId};${resourceGroup().name};${project.name}'

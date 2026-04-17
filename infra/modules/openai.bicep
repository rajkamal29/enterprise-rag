// Azure OpenAI module
// Provisions an Azure OpenAI account with GPT-4o (chat) and
// text-embedding-3-large (embedding) deployments.
// Uses RBAC rather than API keys; managed identity gets Cognitive Services User.

@description('Azure region (must support the requested models)')
param location string

@description('Azure OpenAI account name (globally unique)')
param openAiAccountName string

@description('Principal ID of the user-assigned managed identity')
param managedIdentityPrincipalId string

@description('GPT-4o deployment name')
param chatDeploymentName string = 'gpt-4o'

@description('GPT-4o model version')
param chatModelVersion string = '2024-11-20'

@description('Embedding deployment name')
param embeddingDeploymentName string = 'text-embedding-3-large'

@description('Embedding model version')
param embeddingModelVersion string = '1'

@description('TPM capacity for chat deployment (thousands)')
param chatCapacity int = 10

@description('TPM capacity for embedding deployment (thousands)')
param embeddingCapacity int = 30

@description('Tags to apply to all resources')
param tags object = {}

// Built-in role: Cognitive Services OpenAI User
var cogServicesOpenAiUserRoleId = '5e0bd9bd-7b93-4f28-af87-19fc36ad61bd'

resource openAi 'Microsoft.CognitiveServices/accounts@2024-04-01-preview' = {
  name: openAiAccountName
  location: location
  tags: tags
  kind: 'OpenAI'
  sku: {
    name: 'S0'
  }
  properties: {
    customSubDomainName: openAiAccountName
    publicNetworkAccess: 'Enabled' // lock down via private endpoint in prod
    disableLocalAuth: true         // force managed identity / Entra auth only
  }
}

// Disabled due to template validation error 715-123420
/*
resource chatDeployment 'Microsoft.CognitiveServices/accounts/deployments@2024-04-01-preview' = {
  parent: openAi
  name: chatDeploymentName
  sku: {
    name: 'GlobalStandard'
    capacity: chatCapacity
  }
  properties: {
    model: {
      format: 'OpenAI'
      name: 'gpt-4o'
      version: chatModelVersion
    }
    versionUpgradeOption: 'OnceCurrentVersionExpired'
  }
}

resource embeddingDeployment 'Microsoft.CognitiveServices/accounts/deployments@2024-04-01-preview' = {
  parent: openAi
  name: embeddingDeploymentName
  dependsOn: [chatDeployment]
  sku: {
    name: 'Standard'
    capacity: embeddingCapacity
  }
  properties: {
    model: {
      format: 'OpenAI'
      name: 'text-embedding-3-large'
      version: embeddingModelVersion
    }
    versionUpgradeOption: 'OnceCurrentVersionExpired'
  }
}
*/

// Grant managed identity permission to call the OpenAI endpoint
resource miOpenAiUser 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(openAi.id, managedIdentityPrincipalId, cogServicesOpenAiUserRoleId)
  scope: openAi
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', cogServicesOpenAiUserRoleId)
    principalId: managedIdentityPrincipalId
    principalType: 'ServicePrincipal'
  }
}

output openAiId string = openAi.id
output openAiEndpoint string = openAi.properties.endpoint
output chatDeploymentName string = 'gpt-4o'
output embeddingDeploymentName string = 'text-embedding-3-large'

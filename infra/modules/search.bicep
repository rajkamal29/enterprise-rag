// Azure AI Search module
// Standard tier (S1) with semantic ranking enabled.
// Managed identity gets Search Index Data Contributor for read/write.

@description('Azure region')
param location string

@description('AI Search service name (globally unique)')
param searchServiceName string

@description('Principal ID of the user-assigned managed identity')
param managedIdentityPrincipalId string

@description('Replica count (1 = dev, >=2 = prod HA)')
param replicaCount int = 1

@description('Partition count (1 = dev, scale out for throughput)')
param partitionCount int = 1

@description('Tags to apply to all resources')
param tags object = {}

// Built-in role: Search Index Data Contributor
var searchIndexDataContributorRoleId = '8ebe5a00-799e-43f5-93ac-243d3dce84a7'
// Built-in role: Search Service Contributor
var searchServiceContributorRoleId = '7ca78c08-252a-4471-8644-bb5ff32d4ba0'

resource searchService 'Microsoft.Search/searchServices@2024-03-01-preview' = {
  name: searchServiceName
  location: location
  tags: tags
  sku: {
    name: 'standard'
  }
  properties: {
    replicaCount: replicaCount
    partitionCount: partitionCount
    hostingMode: 'default'
    publicNetworkAccess: 'Enabled'
    disableLocalAuth: true            // force Entra ID authentication
    semanticSearch: 'standard'        // enable semantic ranking
  }
}

// Managed identity: Search Index Data Contributor (read + write index docs)
resource miSearchIndexContributor 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(searchService.id, managedIdentityPrincipalId, searchIndexDataContributorRoleId)
  scope: searchService
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', searchIndexDataContributorRoleId)
    principalId: managedIdentityPrincipalId
    principalType: 'ServicePrincipal'
  }
}

// Managed identity: Search Service Contributor (create/manage indexes)
resource miSearchServiceContributor 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(searchService.id, managedIdentityPrincipalId, searchServiceContributorRoleId)
  scope: searchService
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', searchServiceContributorRoleId)
    principalId: managedIdentityPrincipalId
    principalType: 'ServicePrincipal'
  }
}

output searchServiceId string = searchService.id
output searchServiceEndpoint string = 'https://${searchService.name}.search.windows.net'
output searchServiceName string = searchService.name

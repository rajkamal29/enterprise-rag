// Azure Document Intelligence for document parsing and extraction
// Used by Day 3 ingestion pipeline for chunking and embedding

@description('Azure region')
param location string

@description('Document Intelligence service name')
param documentIntelligenceName string

@description('Managed Identity principal ID for RBAC')
param managedIdentityPrincipalId string

@description('Resource tags')
param tags object

// Azure Document Intelligence (Cognitive Service)
// Supports PDF, DOCX, HTML, TIF, PNG, JPG, etc.
// Uses RBAC for authentication (via Managed Identity)
resource documentIntelligence 'Microsoft.CognitiveServices/accounts@2024-04-01' = {
  name: documentIntelligenceName
  location: location
  kind: 'FormRecognizer'
  sku: {
    name: 'S0'  // Standard SKU for production; change to F0 for free tier (rate-limited)
  }
  identity: {
    type: 'None'  // Using Managed Identity at call site for auth
  }
  properties: {
    // Document Intelligence is RBAC-only in 2024 API versions
    publicNetworkAccess: 'Enabled'
  }
  tags: tags
}

// Grant Managed Identity permission to use Document Intelligence
// Role: Cognitive Services User
resource miDocIntelligenceRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: documentIntelligence
  name: guid(documentIntelligence.id, 'CognitiveServicesUser')
  properties: {
    principalId: managedIdentityPrincipalId
    roleDefinitionId: subscriptionResourceId(
      'Microsoft.Authorization/roleDefinitions',
      '36243c78-bf99-498c-9df9-86d9f8d28e13'  // Cognitive Services User
    )
  }
}

@description('Document Intelligence service ID')
output documentIntelligenceId string = documentIntelligence.id

@description('Document Intelligence endpoint URL')
output documentIntelligenceEndpoint string = documentIntelligence.properties.endpoint

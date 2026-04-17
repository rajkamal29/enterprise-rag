// Managed Identity module
// Creates a user-assigned managed identity used by all services.
// Using user-assigned (not system-assigned) so the same identity can
// be attached to multiple resources and pre-authorized before deployment.

@description('Azure region for all resources')
param location string

@description('Name for the user-assigned managed identity')
param identityName string

@description('Tags to apply to all resources')
param tags object = {}

resource identity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: identityName
  location: location
  tags: tags
}

output identityId string = identity.id
output principalId string = identity.properties.principalId
output clientId string = identity.properties.clientId

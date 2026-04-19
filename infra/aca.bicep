// Day 9 deployment module: ACR + ACA + APIM for Track B runtime
// Deploy with az deployment group create -f infra/aca.bicep -p ...

targetScope = 'resourceGroup'

@description('Short environment name used as suffix (dev | staging | prod)')
@allowed(['dev', 'staging', 'prod'])
param environment string = 'dev'

@description('Azure region for resources')
param location string = resourceGroup().location

@description('Project prefix used in names')
@maxLength(8)
param projectPrefix string = 'erag'

@description('Container image tag for the API runtime')
param imageTag string = 'day9'

@description('Azure OpenAI endpoint URL for runtime configuration')
param azureOpenAiEndpoint string

@description('Azure OpenAI API version')
param azureOpenAiApiVersion string = '2024-08-01-preview'

@description('Azure OpenAI chat deployment name')
param azureOpenAiChatDeployment string = 'gpt-4o'

@description('Azure AI Search endpoint URL for runtime configuration')
param azureSearchEndpoint string

@description('Azure AI Search index name')
param azureSearchIndexName string = 'rag-index'

var suffix = '${projectPrefix}-${environment}'
var acrName = toLower(replace('acr${projectPrefix}${environment}', '-', ''))
var logAnalyticsName = 'log-${suffix}'
var envName = 'acaenv-${suffix}'
var appName = 'aca-rag-${suffix}'
var apimName = 'apim-${suffix}'
var acrLoginServer = '${acrName}.azurecr.io'

var tags = {
  environment: environment
  project: 'enterprise-rag'
  managedBy: 'bicep'
}

resource uami 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: 'id-aca-${suffix}'
  location: location
  tags: tags
}

resource acr 'Microsoft.ContainerRegistry/registries@2023-11-01-preview' = {
  name: acrName
  location: location
  sku: {
    name: 'Basic'
  }
  properties: {
    adminUserEnabled: false
  }
  tags: tags
}

resource logAnalytics 'Microsoft.OperationalInsights/workspaces@2022-10-01' = {
  name: logAnalyticsName
  location: location
  properties: {
    retentionInDays: 30
    sku: {
      name: 'PerGB2018'
    }
  }
  tags: tags
}

resource managedEnvironment 'Microsoft.App/managedEnvironments@2024-03-01' = {
  name: envName
  location: location
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: logAnalytics.properties.customerId
        sharedKey: listKeys(logAnalytics.id, logAnalytics.apiVersion).primarySharedKey
      }
    }
  }
  tags: tags
}

resource containerApp 'Microsoft.App/containerApps@2024-03-01' = {
  name: appName
  location: location
  dependsOn: [acrPullRoleAssignment]
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${uami.id}': {}
    }
  }
  properties: {
    managedEnvironmentId: managedEnvironment.id
    configuration: {
      ingress: {
        external: true
        targetPort: 8000
        transport: 'auto'
      }
      registries: [
        {
          server: acrLoginServer
          identity: uami.id
        }
      ]
    }
    template: {
      containers: [
        {
          name: 'api'
          image: '${acrLoginServer}/enterprise-rag-api:${imageTag}'
          resources: {
            cpu: json('0.5')
            memory: '1.0Gi'
          }
          probes: [
            {
              type: 'Startup'
              httpGet: {
                path: '/health'
                port: 8000
              }
              initialDelaySeconds: 5
              periodSeconds: 5
              timeoutSeconds: 3
              failureThreshold: 24
            }
            {
              type: 'Liveness'
              httpGet: {
                path: '/health'
                port: 8000
              }
              initialDelaySeconds: 10
              periodSeconds: 10
              timeoutSeconds: 3
              failureThreshold: 3
            }
            {
              type: 'Readiness'
              httpGet: {
                path: '/health'
                port: 8000
              }
              initialDelaySeconds: 10
              periodSeconds: 10
              timeoutSeconds: 3
              failureThreshold: 3
            }
          ]
          env: [
            {
              name: 'AZURE_CLIENT_ID'
              value: uami.properties.clientId
            }
            {
              name: 'AZURE_OPENAI_ENDPOINT'
              value: azureOpenAiEndpoint
            }
            {
              name: 'AZURE_OPENAI_API_VERSION'
              value: azureOpenAiApiVersion
            }
            {
              name: 'AZURE_OPENAI_CHAT_DEPLOYMENT'
              value: azureOpenAiChatDeployment
            }
            {
              name: 'AZURE_SEARCH_ENDPOINT'
              value: azureSearchEndpoint
            }
            {
              name: 'AZURE_SEARCH_INDEX_NAME'
              value: azureSearchIndexName
            }
          ]
        }
      ]
      scale: {
        minReplicas: 1
        maxReplicas: 3
        rules: [
          {
            name: 'http-concurrency'
            http: {
              metadata: {
                concurrentRequests: '20'
              }
            }
          }
        ]
      }
    }
  }
  tags: tags
}

resource acrPullRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(acr.id, uami.id, 'acrpull')
  scope: acr
  properties: {
    roleDefinitionId: subscriptionResourceId(
      'Microsoft.Authorization/roleDefinitions',
      '7f951dda-4ed3-4680-a7ca-43fe172d538d'
    )
    principalId: uami.properties.principalId
    principalType: 'ServicePrincipal'
  }
}

resource apim 'Microsoft.ApiManagement/service@2023-05-01-preview' = {
  name: apimName
  location: location
  sku: {
    name: 'Consumption'
    capacity: 0
  }
  properties: {
    publisherEmail: 'noreply@contoso.com'
    publisherName: 'Enterprise RAG'
  }
  tags: tags
}

resource apimApi 'Microsoft.ApiManagement/service/apis@2023-05-01-preview' = {
  parent: apim
  name: 'rag-api'
  properties: {
    displayName: 'Enterprise RAG API'
    path: 'rag'
    subscriptionRequired: true
    protocols: [
      'https'
    ]
    serviceUrl: 'https://${containerApp.properties.configuration.ingress.fqdn}'
  }
}

resource apimOperation 'Microsoft.ApiManagement/service/apis/operations@2023-05-01-preview' = {
  parent: apimApi
  name: 'ask'
  properties: {
    displayName: 'Ask'
    method: 'POST'
    urlTemplate: '/ask'
    request: {
      description: 'Ask question against LangGraph RAG runtime.'
      queryParameters: []
      headers: []
      representations: [
        {
          contentType: 'application/json'
        }
      ]
    }
    responses: [
      {
        statusCode: 200
        representations: [
          {
            contentType: 'application/json'
          }
        ]
      }
    ]
  }
}

resource apimHealthOperation 'Microsoft.ApiManagement/service/apis/operations@2023-05-01-preview' = {
  parent: apimApi
  name: 'health'
  properties: {
    displayName: 'Health'
    method: 'GET'
    urlTemplate: '/health'
    responses: [
      {
        statusCode: 200
        representations: [
          {
            contentType: 'application/json'
          }
        ]
      }
    ]
  }
}

resource apimPolicy 'Microsoft.ApiManagement/service/apis/policies@2023-05-01-preview' = {
  parent: apimApi
  name: 'policy'
  properties: {
    format: 'rawxml'
    value: '<policies><inbound><base /><set-backend-service base-url="https://${containerApp.properties.configuration.ingress.fqdn}" /><set-variable name="callerKey" value="@(context.Subscription != null ? context.Subscription.Key : context.Request.IpAddress)" /><rate-limit-by-key calls="60" renewal-period="60" counter-key="@(context.Variables.GetValueOrDefault<string>("callerKey", context.Request.IpAddress))" /><quota-by-key calls="10000" renewal-period="86400" counter-key="@(context.Variables.GetValueOrDefault<string>("callerKey", context.Request.IpAddress))" /></inbound><backend><base /></backend><outbound><base /><set-header name="X-Content-Type-Options" exists-action="override"><value>nosniff</value></set-header><set-header name="Strict-Transport-Security" exists-action="override"><value>max-age=31536000; includeSubDomains</value></set-header></outbound><on-error><base /></on-error></policies>'
  }
}

output acrLoginServer string = acrLoginServer
output containerAppFqdn string = containerApp.properties.configuration.ingress.fqdn
output containerAppIdentityPrincipalId string = uami.properties.principalId
output apimGatewayUrl string = apim.properties.gatewayUrl

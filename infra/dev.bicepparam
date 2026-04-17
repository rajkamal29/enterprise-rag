using './main.bicep'

// ── Dev environment parameters ───────────────────────────────────────────────
// Adjust these values before deploying.

param environment = 'dev'
param location = 'eastus'
param projectPrefix = 'erag'

// Set to your Entra ID object ID so you can read/write Key Vault secrets locally.
// Retrieve with: az ad signed-in-user show --query id -o tsv
param deployerPrincipalId = ''

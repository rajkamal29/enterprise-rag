"""
Grant the Search service's system-assigned managed identity the
'Cognitive Services OpenAI User' role on the Azure OpenAI resource,
so the integrated vectorizer can authenticate.
"""
import json
import urllib.request
import uuid

from azure.identity import DefaultAzureCredential

credential = DefaultAzureCredential()
token = credential.get_token("https://management.azure.com/.default").token

sub = "13400920-fd6c-49a2-b559-13d663a72601"
rg = "rg-erag-dev"

# 1. Get Search service system-assigned identity
search_url = (
    f"https://management.azure.com/subscriptions/{sub}/resourceGroups/{rg}"
    f"/providers/Microsoft.Search/searchServices/srch-erag2-dev?api-version=2023-11-01"
)
req = urllib.request.Request(search_url, headers={"Authorization": f"Bearer {token}"})
with urllib.request.urlopen(req) as resp:
    search_data = json.loads(resp.read())

search_identity = search_data.get("identity", {})
search_principal_id = search_identity.get("principalId")
print(f"Search identity type: {search_identity.get('type')}")
print(f"Search principal ID:  {search_principal_id}")

if not search_principal_id:
    print("Search service has no system-assigned identity. Enabling it...")
    # Enable system-assigned identity on search service
    patch_body = json.dumps({"identity": {"type": "SystemAssigned"}}).encode()
    patch_req = urllib.request.Request(
        search_url,
        data=patch_body,
        method="PATCH",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(patch_req) as resp:
        patch_data = json.loads(resp.read())
    search_principal_id = patch_data.get("identity", {}).get("principalId")
    print(f"Enabled. New principal ID: {search_principal_id}")

# 2. Get OpenAI resource ID
oai_url = (
    f"https://management.azure.com/subscriptions/{sub}/resourceGroups/{rg}"
    f"/providers/Microsoft.CognitiveServices/accounts/oai-erag2-dev?api-version=2023-05-01"
)
req2 = urllib.request.Request(oai_url, headers={"Authorization": f"Bearer {token}"})
with urllib.request.urlopen(req2) as resp2:
    oai_data = json.loads(resp2.read())
oai_resource_id = oai_data["id"]
print(f"OpenAI resource ID: {oai_resource_id}")

# 3. Assign Cognitive Services OpenAI User role
# Role ID: 5e0bd9bd-7b93-4f28-af87-19fc36ad61bd
_role_def_guid = "5e0bd9bd-7b93-4f28-af87-19fc36ad61bd"
role_def_id = (
    f"/subscriptions/{sub}/providers/Microsoft.Authorization"
    f"/roleDefinitions/{_role_def_guid}"
)
assignment_id = str(uuid.uuid4())
assignment_url = (
    f"https://management.azure.com{oai_resource_id}/providers/Microsoft.Authorization"
    f"/roleAssignments/{assignment_id}?api-version=2022-04-01"
)
body = json.dumps({
    "properties": {
        "roleDefinitionId": role_def_id,
        "principalId": search_principal_id,
        "principalType": "ServicePrincipal",
    }
}).encode()

assign_req = urllib.request.Request(
    assignment_url,
    data=body,
    method="PUT",
    headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
)
try:
    with urllib.request.urlopen(assign_req) as resp3:
        result = json.loads(resp3.read())
    print(f"Role assigned! Assignment ID: {result['name']}")
except urllib.error.HTTPError as e:
    err = json.loads(e.read())
    if err.get("error", {}).get("code") == "RoleAssignmentExists":
        print("Role already assigned.")
    else:
        raise

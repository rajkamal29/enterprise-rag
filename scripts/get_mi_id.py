import json
import urllib.request

from azure.identity import DefaultAzureCredential

credential = DefaultAzureCredential()
token = credential.get_token("https://management.azure.com/.default").token

sub = "13400920-fd6c-49a2-b559-13d663a72601"
rg = "rg-erag-dev"
ws = "proj-erag2-dev"

url = (
    f"https://management.azure.com/subscriptions/{sub}/resourceGroups/{rg}"
    f"/providers/Microsoft.MachineLearningServices/workspaces/{ws}?api-version=2024-04-01"
)
req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
with urllib.request.urlopen(req) as resp:
    data = json.loads(resp.read())

identity = data.get("identity", {})
print("Identity type:", identity.get("type"))
print("System-assigned principal ID:", identity.get("principalId"))
for k, v in identity.get("userAssignedIdentities", {}).items():
    print(f"  UAI resource: {k}")
    cid = v.get("clientId")
    pid = v.get("principalId")
    print(f"    clientId:    {cid}")
    print(f"    principalId: {pid}")

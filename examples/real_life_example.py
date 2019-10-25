import logging
from random import randint
import re
import time

from tfc_client import TFCClient

from example_config import org_id, token, github_oauth, null_resource_project, test_ws_prefix

# logging.basicConfig(level=logging.DEBUG)

client = TFCClient(token)
tfc = client.get_organization(org_id)

print("Connected on organization id:", tfc.name)

print("List the 5 first workspaces")
count = 0
for ws in tfc.workspaces:
    print("workspace name:", ws.name)
    print(" - latest-change-at:", ws.latest_change_at)
    print("   vcs_repo:", ws.vcs_repo)
    print(" - Retreive lastest run...")
    try:
        print("   - message =>", ws.latest_run.message)
        print("   - status =>", ws.latest_run.status)
    except AttributeError:
        pass
    print(" - List variables")

    print("   -->", ", ".join(ws.variables.keys()))

    print("=========================================")
    count += 1
    if count >= 5:
        break

ws_name = "{}{:05d}".format(test_ws_prefix, randint(1, 99999))
print(f"Creating workspace {ws_name}")
workspace = {
    "name": ws_name,
    "terraform-version": "0.11.10",
    "working-directory": "",
    "vcs-repo": {
        "identifier": null_resource_project,
        "oauth-token-id": github_oauth,
        "branch": "master",
        "default-branch": True,
    },
}

new_ws = tfc.create_workspace(workspace)

ws_by_id = tfc.workspace(workspace_id=new_ws.id)
print("ws_by_id:", ws_by_id.name)

ws_by_name = tfc.workspace(workspace_name=new_ws.name)
print("ws_by_name:", ws_by_name.name)

# Create variable "bar"
new_ws.create_variable(key="bar", value="test")


print("Create a run...")
my_run = new_ws.create_run(message="First Try !")

my_run.wait_run(sleep_time=2, timeout=10)


# print(org.workspace(new_ws.id).name)
input("Press Enter to continue...")

for ws in tfc.workspaces:
    if re.match(test_ws_prefix + r"\d{5}", ws.name):
        print("delete", ws.id, ws.name)
        tfc.delete_workspace(ws.id)


# lz-gcp-opus-prod-west3-dtep

# print("Org name:", org.name)
# print("perm", org.permissions.can_destroy)

# for workspace in client.list_workspaces():
#     print(workspace.id, workspace.name)

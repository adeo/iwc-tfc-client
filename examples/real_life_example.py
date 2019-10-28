import logging
from random import randint
import re
import time

from tfc_client import TFCClient

from tfc_client.models.vcs_repo import VCSRepoModel
from tfc_client.models.workspace import WorkspaceModel
from tfc_client.models.organization import OrganizationModel


from example_config import (
    org_id,
    user_token,
    team_token,
    github_oauth,
    null_resource_project,
    test_ws_prefix,
    test_org_prefix,
    test_org_email,
)

# logging.basicConfig(level=logging.DEBUG)

if user_token:
    admin_client = TFCClient(user_token)

    org_name = "{}{:05d}".format(test_org_prefix, randint(1, 99999))
    print(f"Creating organization '{org_name}'")
    org_model = OrganizationModel(name=org_name, email=test_org_email)
    admin_client.create_organization(org_model)

    input("Press Enter to continue...")

    print(f"Delete organization '{org_name}'")

    admin_client.destroy_organization(org_name)


client = TFCClient(team_token)

print(f"OAuth-token: {github_oauth}")
ot = client.get_oauth_token(github_oauth)
print(ot.created_at)

tfc = client.get_organization(org_id)
print(f"Now connected on organization '{tfc.name}' with Team Token")


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

vcs_repo = VCSRepoModel(
    identifier=null_resource_project,
    oauth_token_id=github_oauth,
    branch="master",
    default_branch=True,
)

workspace_to_create = WorkspaceModel(
    name=ws_name, terraform_version="0.11.10", working_directory="", vcs_repo=vcs_repo
)

new_ws = tfc.create_workspace(workspace_to_create)

ws_by_id = tfc.workspace(workspace_id=new_ws.id)
print("ws_by_id:", ws_by_id.name)

ws_by_name = tfc.workspace(workspace_name=new_ws.name)
print("ws_by_name:", ws_by_name.name)

print("Add a variable 'bar' ..." )
new_ws.create_variable(key="bar", value="test")

print("Create a run...")
my_run = new_ws.create_run(message="First Try !")

my_run.wait_run(
    sleep_time=2,
    timeout=200,
    target_status="planned",
    callback=lambda duration, timeout, status: print(
        f"wait_run ... duration: {duration:.2f}/{timeout}s (status: {status})"
    ),
)

input("Press Enter to apply...")

my_run.apply(comment="Auto apply from TFC Client")

my_run.wait_run(
    sleep_time=2,
    timeout=200,
    target_status="applied",
    callback=lambda duration, timeout, status: print(
        f"wait_run ... duration: {duration:.2f}/{timeout}s (status: {status})"
    ),
)
input("Press Enter to delete test workspacess...")

for ws in tfc.workspaces:
    if re.match(test_ws_prefix + r"\d{5}", ws.name):
        print("delete", ws.id, ws.name)
        tfc.delete_workspace(ws.id)

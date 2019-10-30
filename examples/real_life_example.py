import logging
from random import randint
import re
import time

from tfc_client import TFCClient, RunStatus

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
for ws in tfc.workspaces_search(include_relationship="current-run"):
    print("workspace name:", ws.name)
    print(" - latest-change-at:", ws.latest_change_at)
    print("   vcs_repo:", ws.vcs_repo)
    print(" - Retreive current run...")
    try:
        print("   - message =>", ws.current_run.message)
        print("   - status =>", ws.current_run.status)
    except AttributeError:
        pass
    print(" - List variables")
    print("   -->", ", ".join(ws.variables.keys()))

    # print(" - List runs")
    # for run in ws.runs:
    #     print("    •", run.status, run.created_at)

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

ws_by_id = client.get_workspace(id=new_ws.id)
print("ws_by_id:", ws_by_id.name)

ws_by_name = tfc.workspace(name=new_ws.name)
print("ws_by_name:", ws_by_name.name)

print("Add a variable 'bar' ...")
new_ws.create_variable(key="bar", value="test")

print("Create a run...")
my_run = new_ws.create_run(message="First Try !")

def goto_line(nb):
    return f"\x1b[{nb}A"

clear_after = "\x1b[K"

def tail_plan_log(duration, status, run):
    nb_lines = 10
    print("============================8<===================================")
    print("\n"*nb_lines, end="")
    print(f"{goto_line(nb_lines)}", end="")
    last_lines = run.plan.log_colored.splitlines()[-nb_lines:]
    print(f"{clear_after}\n".join(last_lines))
    if len(last_lines) < nb_lines:
        print(f"{clear_after}\n"*(nb_lines-len(last_lines)), end="")
    print("============================8<===================================")
    print(f"{goto_line(nb_lines+2)}", end="")


def tail_plan_log_finish(duration, status, run):
    nb_lines = 10
    print("\n"*(nb_lines+1), end="")

def tail_apply_log(duration, status, run):
    nb_lines = 10
    print("============================8<===================================")
    print("\n"*nb_lines, end="")
    print(f"{goto_line(nb_lines)}", end="")
    last_lines = run.apply.log_colored.splitlines()[-nb_lines:]
    print(f"{clear_after}\n".join(last_lines))
    if len(last_lines) < nb_lines:
        print(f"{clear_after}\n"*(nb_lines-len(last_lines)), end="")
    print("============================8<===================================")
    print(f"{goto_line(nb_lines+2)}", end="")

def tail_apply_log_finish(duration, status, run):
    nb_lines = 10
    print("\n"*(nb_lines+1), end="")

my_run.wait_run(
    sleep_time=1,
    timeout=200,
    progress_callback=tail_plan_log,
    target_callback=tail_plan_log_finish,
)

input(f"Press Enter to apply...{clear_after}")

my_run.do_apply(comment="Auto apply from TFC Client")

my_run.wait_run(
    sleep_time=1,
    timeout=200,
    target_status=[ RunStatus.planned_and_finished, RunStatus.errored, RunStatus.applied],
    progress_callback=tail_apply_log,
    target_callback=tail_apply_log_finish,
)
input(f"Press Enter to delete test workspacess...{clear_after}")

for ws in tfc.workspaces_search(search=test_ws_prefix):
    if re.match(test_ws_prefix + r"\d{5}", ws.name):
        print("delete", ws.id, ws.name)
        tfc.delete_workspace(ws.id)

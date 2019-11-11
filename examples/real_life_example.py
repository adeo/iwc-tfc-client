import logging
from random import randint
import re
import time

from tfc_client import TFCClient
from tfc_client.enums import (
    RunStatus,
    WorkspaceSort,
    NotificationTrigger,
    NotificationsDestinationType,
)

from tfc_client.models.workspace import VCSRepoModel
import tfc_client.exception

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


def goto_line(nb):
    return f"\x1b[{nb}A"


clear_after = "\x1b[K"


# logging.basicConfig(level=logging.DEBUG)

if user_token:
    admin_client = TFCClient(user_token)

    org_name = "{}{:05d}".format(test_org_prefix, randint(1, 99999))
    print(f"Creating organization '{org_name}'")
    new_org = admin_client.create_organization(name=org_name, email=test_org_email)

    print(
        f"org name: {new_org.name} param 'session_timeout' is '{new_org.session_timeout}'"
    )
    print("Modifying the paramter session-timeout")
    new_org.modify(session_timeout=1000)
    print("Rename the org (add a _new)")
    new_org.modify(name=org_name + "_new")
    print(
        f"org name: {new_org.name} param 'session_timeout' is '{new_org.session_timeout}'"
    )
    input("Press Enter to continue...")

    for org in admin_client.organizations:
        if re.match(test_org_prefix + r"\d{5}", org.name):
            admin_client.destroy_organization(org.name)
            print("-", org.name)
        else:
            print("*", org.name)

client = TFCClient(team_token)

print(f"OAuth-token: {github_oauth}")
ot = client.get("oauth-token", github_oauth)
print(ot.created_at)


my_org = client.get("organization", org_id)

print(f"Now connected on organization '{my_org.name}' with Team Token")

print("Create an ssh_key")
sshkey_name = "{}{:05d}".format(test_org_prefix + "sshkey", randint(1, 99999))
my_sshkey = my_org.create(
    "ssh-key",
    name=sshkey_name,
    value="-----BEGIN RSA PRIVATE KEY-----\nMIIEowIBAAKCAQEAm6+JVgl...",
)

print("List the 5 first workspaces")
for ws in my_org.workspaces_search(
    include="current-run", limit=5, sort=WorkspaceSort.current_run
):
    print("workspace name:", ws.name)
    print(" - latest-change-at:", ws.latest_change_at)
    print("   vcs_repo:", ws.vcs_repo)
    print(" - current run info...")
    try:
        print("   - created-at => ", ws.current_run.created_at)
        print("   - message =>", ws.current_run.message)
        print("   - status =>", ws.current_run.status)
    except AttributeError:
        pass
    print(" - List variables")
    print("   -->", ", ".join([var.key for var in ws.vars]))

    print(" - List runs")
    for run in ws.runs:
        print("    •", run.status, run.created_at)

    print("=========================================")

ws_name = "{}{:05d}".format(test_ws_prefix, randint(1, 99999))
print(f"Creating workspace {ws_name}")

vcs_repo = VCSRepoModel(
    identifier=null_resource_project,
    oauth_token_id=github_oauth,
    branch="master",
    default_branch=True,
)

new_ws = my_org.create("workspace", name=ws_name, vcs_repo=vcs_repo)

print("Create a Notification configuration")
my_notification = new_ws.create(
    "notification-configuration",
    enabled=True,
    name="MyNotif",
    url="https://httpstat.us/200",
    destination_type=NotificationsDestinationType.generic,
    token="TestToken",
    triggers=[NotificationTrigger.created],
)

for nc in new_ws.get_list("notification-configurations"):
    print(" * Notification:", nc.name)
    for nc_delivery in nc.delivery_responses:
        print("   - {url} {code} {successful}".format(**nc_delivery))

my_notification.do_verify()

for nc in new_ws.get_list("notification-configurations"):
    print(" * Notification:", nc.name)
    for nc_delivery in nc.delivery_responses:
        print("   - {url} {code} {successful}".format(**nc_delivery))


print(
    f"Check version of workspace named '{new_ws.name}': {new_ws.terraform_version} (default value)"
)

new_ws.modify(terraform_version="0.11.10")
print(
    f"After modifying version of workspace named '{new_ws.name}': {new_ws.terraform_version}"
)

print(f"Assign ssh-key {my_sshkey.name}")
new_ws.assign("ssh-key", my_sshkey)
input(
    f"check ssh-key here: https://app.terraform.io/app/{my_org.id}/workspaces/{new_ws.name}/settings/ssh. Press Enter to continue..."
)

new_ws.unassign("ssh-key")
input(
    f"check unassigned key here: https://app.terraform.io/app/{my_org.id}/workspaces/{new_ws.name}/settings/ssh. Press Enter to continue..."
)

for sshkey in my_org.ssh_keys:
    print("sshkey:", sshkey.id)
    if re.match(test_org_prefix + "sshkey" + r"\d{5}", sshkey.name):
        my_org.delete(sshkey)

input(
    f"Check that all SSH Keys matching '{test_org_prefix}sshkey' are deleted from the org : https://app.terraform.io/app/{my_org.id}/settings/manage-ssh-keys. Press Enter to continue..."
)

ws_by_id = client.get("workspace", id=new_ws.id)
print("ws_by_id:", ws_by_id.name)

ws_by_name = my_org.workspace(name=new_ws.name)
print("ws_by_name:", ws_by_name.name)

print("Add a variable 'bar' ...")

my_var = new_ws.create("var", key="bar", value="test")
my_var_to_delete = new_ws.create("var", key="todelete", value="dontchangeme")

print(f"my_var named {my_var.key} = '{my_var.value}'")
my_var.modify(value="toto")
print(f"after modify, my_var named {my_var.key} = '{my_var.value}'")
new_ws.delete(my_var_to_delete)
input(
    f"Check variables here: https://app.terraform.io/app/{my_org.id}/workspaces/{new_ws.name}/variables. Press Enter to continue..."
)

print("Create a run...")
my_run = new_ws.create("run", message="First Try !")


def tail_plan_log(duration, run):
    nb_lines = 10
    print(
        f"============================ {run.status} ==================================="
    )
    print("\n" * nb_lines, end="")
    print(f"{goto_line(nb_lines)}", end="")
    last_lines = run.plan.log_colored.splitlines()[-nb_lines:]
    print(f"{clear_after}\n".join(last_lines))
    if len(last_lines) < nb_lines:
        print(f"{clear_after}\n" * (nb_lines - len(last_lines)), end="")
    print("============================8<===================================")
    print(f"{goto_line(nb_lines+2)}", end="")


def tail_apply_log(duration, run):
    nb_lines = 10
    print(
        f"============================ {run.status} ==================================="
    )
    print("\n" * nb_lines, end="")
    print(f"{goto_line(nb_lines)}", end="")
    last_lines = run.apply.log_colored.splitlines()[-nb_lines:]
    print(f"{clear_after}\n".join(last_lines))
    if len(last_lines) < nb_lines:
        print(f"{clear_after}\n" * (nb_lines - len(last_lines)), end="")
    print("============================8<===================================")
    print(f"{goto_line(nb_lines+2)}", end="")


my_run.wait_plan(sleep_time=1, timeout=200, progress_callback=tail_plan_log)
print("\n" * 11)

input(f"Press Enter to apply...{clear_after}")
try:
    my_run.do_apply(comment="Auto apply from TFC Client")

    my_run.wait_apply(sleep_time=1, timeout=200, progress_callback=tail_apply_log)
    print("\n" * 11)

    input(f"Press Enter to delete test workspaces...{clear_after}")
except tfc_client.exception.APIException:
    print("Can't apply (plan not finish). Pass...")

for ws in my_org.workspaces_search(search=test_ws_prefix):
    if re.match(test_ws_prefix + r"\d{5}", ws.name):
        print("delete", ws.id, ws.name)
        my_org.delete(ws)

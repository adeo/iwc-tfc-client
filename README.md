# Terraform Cloud API Python Client

Try to offer a good python object interface to Terraform Cloud API.

## Name proposal

kishi : "Earth snake" in Japanese.

## Quick start

You can get all TFC objects by id with :

```python
from tfc_client import TFCClient
from tfc_client.enums import RunStatus
from tfc_client.models import VCSRepoModel, WorkspaceModel

# Instanciate the client
client = TFCClient(token="WXDFR3ZSDFGYTdftredfgtre")

# Retreive any object type by ID from the client
my_org = client.get("organization", id="myorg")
my_ws = client.get("workspace", id="ws-gvcdr54dfd")
my_run = client.get("run", id="run-wvfgkdlz")
my_var = client.get("var", id="var-vcerjvjk")

# If you need to retreive a workspace by name, you need to retreive it from an organization object:
my_ws = my_org.workspace(name="my_workspace")

# To retreive all workspaces:
for ws in my_org.workspaces:
    print(ws.name)

# To retreive a subset of workspaces:
for ws in my_org.workspaces_search(search="my_"):
    print(ws.name)

# If you need to retreive all workspaces with associated current-run info efficiently (in one api call):
for ws in my_org.workspaces_search(include="current-run"):
    print(f"{ws.name} -> {ws.current_run.status}")

# To create a workspace linked with a github repository
# First: Create the repository object:
vcs_repo = VCSRepoModel(
    identifier="github/repo",
    oauth_token_id="ot-fgtredfgtr",
    branch="master",
    default_branch=True,
)
# Secondly: Create a workspace object that include the previous object:
workspace_to_create = WorkspaceModel(
    name="my_workspace_test", terraform_version="0.11.10", working_directory="", vcs_repo=vcs_repo
)
# Finally: Send the workspace object to TFC API:
my_ws = my_org.create_workspace(workspace_to_create)


# Launch a run on a workspace:
my_run = my_ws.create_run(message="Run run run")

# Wait for the run plan execution
if my_run.wait_plan(timeout=200, progress_callback=lambda run, duration: print(f"{run.id} status is {run.status}")):
    print(f"{my_run.id} reached the target status ({my_run.status})")
    # Display log of the plan (with ANSI color)
    print(my_run.plan.log_colored)

else:
    print(f"{my_run.id} is pending. Don't wait...")

if RunStatus(my_run.status) == RunStatus.planned:
    # Launch the Apply
    my_run.do_apply(comment="Apply !")
    # Wait for the run apply execution
    if my_run.wait_apply(timeout=200, progress_callback=lambda run, duration: print(f"{run.id} status is {run.status}")):
        print(f"{my_run.id} reached the target status ({my_run.status})")
        # Display log of the apply (with ANSI color)
        print(my_run.apply.log_colored)
    else:
        print(f"{my_run.id} is pending. Don't wait...")

# To retreive all runs of a workspace:
for run in my_ws.runs:
    print(f"{run.id}: {run.status}")

# Delete the workspace
my_org.delete_workspace(my_ws.id)
```


## Current coverage of the TFC API

Currently the following endpoints are supported:

- [ ] [Account](https://www.terraform.io/docs/enterprise/api/account.html)
- [x] [Applies](https://www.terraform.io/docs/cloud/api/applies.html)
- [ ] [Configuration Versions](https://www.terraform.io/docs/enterprise/api/configuration-versions.html)
- [ ] [Cost Estimates](https://www.terraform.io/docs/cloud/api/cost-estimates.html)
- [ ] [Notification Configurations](terraform.io/docs/cloud/api/notification-configurations.html)
- [ ] [OAuth Clients](https://www.terraform.io/docs/enterprise/api/oauth-clients.html)
- [ ] [OAuth Tokens](https://www.terraform.io/docs/enterprise/api/oauth-tokens.html)
- [x] [Organizations](https://www.terraform.io/docs/enterprise/api/organizations.html)
  - [x] List
  - [x] Show
  - [x] Create
  - [ ] Update
  - [x] Destroy
- [ ] [Organization Tokens](https://www.terraform.io/docs/enterprise/api/organization-tokens.html)
- [ ] [Plan Exports](https://www.terraform.io/docs/cloud/api/plan-exports.html)
- [x] [Plans](https://www.terraform.io/docs/cloud/api/plans.html)
- [ ] [Policies](https://www.terraform.io/docs/enterprise/api/policies.html)
- [ ] [Policy Checks](https://www.terraform.io/docs/enterprise/api/policy-checks.html)
- [ ] [Policy Sets](https://www.terraform.io/docs/enterprise/api/policy-sets.html)
- [ ] [Registry Modules](https://www.terraform.io/docs/enterprise/api/modules.html)
- [x] [Runs](https://www.terraform.io/docs/enterprise/api/run.html)
  - [x] Create
  - [x] Apply
  - [x] List runs in a workspace
  - [x] Get details
  - [x] Discard
  - [x] Cancel
  - [x] Force cancel
  - [x] Force execute
- [ ] [SSH Keys](https://www.terraform.io/docs/enterprise/api/ssh-keys.html)
- [ ] [State Versions](https://www.terraform.io/docs/enterprise/api/state-versions.html)
- [ ] [State Version Outputs](https://www.terraform.io/docs/cloud/api/user-tokens.html)
- [ ] [Team Access](https://www.terraform.io/docs/enterprise/api/team-access.html)
- [ ] [Team Memberships](https://www.terraform.io/docs/enterprise/api/team-members.html)
- [ ] [Team Tokens](https://www.terraform.io/docs/enterprise/api/team-tokens.html)
- [ ] [Teams](https://www.terraform.io/docs/enterprise/api/teams.html)
- [ ] [User Tokens](https://www.terraform.io/docs/cloud/api/user-tokens.html)
- [x] [Users](https://www.terraform.io/docs/cloud/api/users.html)
- [x] [Variables](https://www.terraform.io/docs/enterprise/api/variables.html)
  - [x] Create
  - [x] List
  - [ ] Update
  - [ ] Delete
- [x] [Workspaces](https://www.terraform.io/docs/enterprise/api/workspaces.html)
  - [x] List
  - [x] Show
  - [x] Create
  - [ ] Update
  - [x] Delete
  - [ ] Lock
  - [ ] Unlock
  - [ ] Force Unlock
  - [ ] Assigh SSH key
  - [ ] Unassign SSH key
- [ ] [Admin Organizations](https://www.terraform.io/docs/cloud/api/admin/organizations.html)
- [ ] [Admin Runs](https://www.terraform.io/docs/cloud/api/admin/runs.html)
- [ ] [Admin Settings](https://www.terraform.io/docs/cloud/api/admin/settings.html)
- [ ] [Admin Terraform Versions](https://www.terraform.io/docs/cloud/api/admin/terraform-versions.html)
- [ ] [Admin Users](https://www.terraform.io/docs/cloud/api/admin/users.html)
- [ ] [Admin Workspaces](https://www.terraform.io/docs/cloud/api/admin/workspaces.html)

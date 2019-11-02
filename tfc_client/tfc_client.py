from collections.abc import Mapping, Iterable
import hashlib
import re
import time

from .util import InflectionStr

from .api_caller import APICaller
from .models.relationship import RelationshipsModel
from .models.workspace import WorkspaceRootModel, WorkspaceDataModel, WorkspaceModel
from .models.run import RunRootModel, RunDataModel, RunModel
from .models.var import VarRootModel, VarDataModel, VarModel
from .models.organization import (
    OrganizationRootModel,
    OrganizationDataModel,
    OrganizationModel,
)
from .models.ssh_key import SshKeyRootModel, SshKeyDataModel, SshKeyModel
from .enums import RunStatus, WorkspaceSort, VarCat


class TFCClient(object):
    """The Terraform Cloud Client
    Initialize the session with the API server
    Factory for TFCObject of any valid types with a TFCClient.get_<object_type>(id=<object_id>)
    Can create (and destroy) the root organization object (with a user/admin token. Don't work with a team token)

    Examples:
     - tfc_client.get_workspace(id="ws-12344321")

    :param token: TFC API Token
    :type token: str
    :param url: TFC API URL. Default: "https://app.terraform.io"
    :type url: str
    """

    def __init__(self, token: str, url: str = "https://app.terraform.io"):
        headers = {
            "Content-Type": "application/vnd.api+json",
            "Authorization": "Bearer {}".format(token),
        }
        self._api = APICaller(host=url, base_url="api/v2", headers=headers)

    def get(self, object_type, id):
        object_type = InflectionStr(object_type).dasherize.pluralize
        return TFCObject(self, {"type": object_type, "id": id})

    def __getattr__(self, attr):
        if attr.startswith("get_"):
            object_type = attr[4:]

            def _get_object_type(*args, **kwargs):
                return self.get(
                    object_type, id=kwargs["id"] if "id" in kwargs else args[0]
                )

            return _get_object_type
        else:
            raise AttributeError(attr)

    def create_organization(self, **kwargs):
        organization_model = OrganizationModel(**kwargs)
        payload = OrganizationRootModel(
            data=OrganizationDataModel(
                type="organizations", attributes=organization_model
            )
        )
        api_response = self._api.post(path=f"organizations", data=payload.json())
        return TFCObject(self, api_response.data)

    def destroy_organization(self, organization_name):
        self._api.delete(path=f"organizations/{organization_name}")

    @property
    def organizations(self):
        for api_response in self._api.get_list(path=f"organizations"):
            for org_data in api_response.data:
                yield TFCObject(self, org_data)


class TFCObject(object):
    """Represent a TFC object (workspace, run, variable, plan, apply, organization, ...)
    with all methods to interact with.

    For example:
    - `my_org.workspaces` to retreive all workspaces of an organization
    - `my_workspace.runs` to retreive all runs of a workspace
    - `my_workspace.current_run.do_apply()` to apply the current run of a workspace
    :param client: The TFC Client instance
    :type client: TFCClient
    :param data: Data to initialize the object (content of the "data" object in a API response)
    :type data: dict
    :param include: sub-element to include in the object (like run referenced for a workspace). Valid value depends on the TFC API and the object initialized.
    :type include: str
    :param init_from_data: Fill attributes informations from the data dict. Use False here to init an object from an API patch response, because the returned object is not complete.
    :type init_from_data: bool
    """

    def __init__(self, client, data, include=None, init_from_data=True):
        self.client = client
        self.attrs = dict()
        self.attrs["workspaces"] = dict()
        self.attrs["runs"] = dict()
        self.attrs["vars"] = dict()
        self.attrs["ssh-keys"] = dict()
        self.id = data["id"]
        self.type = data["type"]
        if init_from_data:
            self._init_from_data(data)

        if include and isinstance(include, Iterable):
            for included_data in include:
                for rel_name, rel in self.relationships.items():
                    if rel.id == included_data["id"]:
                        self.relationships[rel_name] = TFCObject(
                            self.client, included_data
                        )

    def _init_from_data(self, data):
        if "attributes" in data:
            self.attributes = data["attributes"]
        if "relationships" in data:
            self.relationships = data["relationships"]
        if "links" in data:
            self.links = data["links"]

    def _get_data(self, element):
        if element not in self.attrs:
            if self.links and "related" in self.links:
                data_url = self.links["related"]
            else:
                data_url = f"{self.type}/{self.id}"

            api_response = self.client._api.get(path=data_url)
            self._init_from_data(api_response.data)

    def refresh(self):
        self.attrs = dict()
        self.attrs["workspaces"] = dict()
        self.attrs["runs"] = dict()
        self.attrs["vars"] = dict()
        self.attrs["ssh-keys"] = dict()

    def factory(self, data):

        class_name = "TFC{type}".format(InflectionStr(data["type"]).singularize.camelize)

    @property
    def attributes(self):
        if "attributes" not in self.attrs:
            self._get_data("attributes")
        return self.attrs["attributes"]

    @attributes.setter
    def attributes(self, attributes_dict):
        self.attrs["attributes"] = attributes_dict

    @property
    def status_counts(self):
        if self.type == "organizations":
            if "status-counts" not in self.attrs:
                api_response = self.client._api.get(
                    path=f"organizations/{self.name}/workspaces",
                    params={"page[size]": 1},
                )
                if "status-counts" in api_response.meta:
                    self.attrs["status-counts"] = api_response.meta["status-counts"]
            return self.attrs.get("status-counts", {})
        else:
            raise AttributeError("status_counts")

    @status_counts.setter
    def status_counts(self, status_counts_dict):
        if self.type == "organizations":
            self.attrs["status-counts"] = status_counts_dict
        else:
            raise AttributeError("status_counts")

    @property
    def pagination(self):
        if self.type in ["organizations", "workspaces"]:
            if "pagination" not in self.attrs:
                api_response = self.client._api.get(
                    path=f"organizations/{self.name}/workspaces",
                    params={"page[size]": 1},
                )
                if "pagination" in api_response.meta:
                    self.attrs["pagination"] = api_response.meta["pagination"]
            return self.attrs.get("pagination", {})
        else:
            raise AttributeError("pagination")

    @pagination.setter
    def pagination(self, pagination_dict):
        if self.type in ["organizations", "workspaces"]:
            self.attrs["pagination"] = pagination_dict
        else:
            raise AttributeError("pagination")

    @property
    def relationships(self):
        if "relationships" not in self.attrs:
            self._get_data("relationships")
        return self.attrs.get("relationships")

    @relationships.setter
    def relationships(self, relationships_dict):
        self.attrs["relationships"] = dict()
        for relationship_key, relationship_value in relationships_dict.items():
            if "data" in relationship_value:
                if isinstance(relationship_value["data"], Mapping):
                    self.attrs["relationships"][relationship_key] = TFCObject(
                        self.client, relationship_value["data"]
                    )
                elif isinstance(relationship_value["data"], Iterable):
                    self.attrs["relationships"][relationship_key] = list()
                    for data in relationship_value["data"]:
                        self.attrs["relationships"][relationship_key].append(
                            TFCObject(self.client, data)
                        )

    @property
    def links(self):
        return self.attrs.get("links")

    @links.setter
    def links(self, links_dict):
        self.attrs["links"] = links_dict

    @property
    def variables(self):
        if self.type == "workspaces":
            if not self.attrs["vars"]:
                for api_response in self.client._api.get_list(
                    path="vars",
                    filters={
                        "workspace": {"name": self.name},
                        "organization": {"name": self.organization.id},
                    },
                ):
                    self.variables = api_response.data
            return self.attrs["vars"]
        else:
            raise AttributeError("variables")

    @variables.setter
    def variables(self, variables_list):
        if self.type == "workspaces":
            for data in variables_list:
                var_object = TFCObject(self.client, data)
                self.attrs["vars"][var_object.key] = var_object
        else:
            raise AttributeError("variables")

    def create_variable(
        self, key, value, category=VarCat.terraform, sensitive=False, hcl=False
    ):
        if self.type == "workspaces":
            payload = VarRootModel(
                data=VarDataModel(
                    type="vars",
                    attributes=VarModel(
                        key=key,
                        value=value,
                        sensitive=sensitive,
                        hcl=hcl,
                        category=category,
                    ),
                    relationships=RelationshipsModel(
                        workspace=WorkspaceRootModel(
                            data=WorkspaceDataModel(type="workspaces", id=self.id)
                        )
                    ),
                )
            )

            api_response = self.client._api.post(path=f"vars", data=payload.json())
            var = TFCObject(self.client, api_response.data)
            self.attrs["vars"][var.id] = var
            return var
        else:
            raise AttributeError("variables")

    @property
    def runs(self):
        if self.type == "workspaces":
            for api_response in self.client._api.get_list(
                path=f"workspaces/{self.id}/runs"
            ):
                if "pagination" in api_response.meta:
                    self.pagination = api_response.meta["pagination"]

                for run in api_response.data:
                    run_id = run["id"]
                    self.attrs["runs"][run_id] = TFCObject(self.client, run)
                    yield self.attrs["runs"][run_id]
        else:
            raise AttributeError("runs")

    @property
    def workspaces(self):
        if self.type == "organizations":
            for api_response in self.client._api.get_list(
                path=f"organizations/{self.name}/workspaces"
            ):
                if "pagination" in api_response.meta:
                    self.pagination = api_response.meta["pagination"]
                if "status-counts" in api_response.meta:
                    self.status_counts = api_response.meta["status-counts"]
                for ws in api_response.data:
                    ws_id = ws["id"]
                    self.attrs["workspaces"][ws_id] = TFCObject(self.client, ws)
                    yield self.attrs["workspaces"][ws_id]
        else:
            raise AttributeError("workspaces")

    @property
    def ssh_keys(self):
        if self.type == "organizations":
            for api_response in self.client._api.get_list(
                path=f"organizations/{self.name}/ssh-keys"
            ):
                if "pagination" in api_response.meta:
                    self.pagination = api_response.meta["pagination"]
                if "status-counts" in api_response.meta:
                    self.status_counts = api_response.meta["status-counts"]
                for ssh_key in api_response.data:
                    ssh_key_id = ssh_key["id"]
                    self.attrs["ssh-keys"][ssh_key_id] = TFCObject(self.client, ssh_key)
                    yield self.attrs["ssh-keys"][ssh_key_id]
        else:
            raise AttributeError("ssh_keys")


    def workspaces_search(
        self, *, search=None, filters=None, include=None, sort=None, limit=None
    ):
        if self.type == "organizations":
            organization = self.name

            if sort and not isinstance(sort, WorkspaceSort):
                sort = WorkspaceSort(sort)

            count = 0
            for api_response in self.client._api.get_list(
                path=f"organizations/{organization}/workspaces",
                include=InflectionStr(include).underscore if include else None,
                search=search,
                filters=filters,
                sort=sort,
            ):
                if "pagination" in api_response.meta:
                    self.pagination = api_response.meta["pagination"]
                if "status-counts" in api_response.meta:
                    self.status_counts = api_response.meta["status-counts"]

                for ws in api_response.data:
                    if isinstance(limit, int) and count >= limit:
                        return
                    ws_id = ws["id"]

                    try:
                        included_rel_id = ws["relationships"][include]["data"]["id"]

                        included_rel_data = [
                            included
                            for included in api_response.included
                            if included["id"] == included_rel_id
                        ]
                    except (KeyError, TypeError):
                        included_rel_data = None

                    if included_rel_data:
                        self.attrs["workspaces"][ws_id] = TFCObject(
                            self.client, ws, include=included_rel_data
                        )
                    else:
                        self.attrs["workspaces"][ws_id] = TFCObject(self.client, ws)
                    yield self.attrs["workspaces"][ws_id]
                    count += 1
        else:
            raise AttributeError("workspaces")

    def workspace(self, name):
        if self.type == "organizations":
            workspace_id = None
            ws_ids = [
                ws_id
                for ws_id, ws in self.attrs["workspaces"].items()
                if ws.name == name
            ]
            if ws_ids:
                workspace_id = ws_ids[0]

            if workspace_id:
                return self.attrs["workspaces"][workspace_id]
            else:
                ws = TFCObject(
                    self.client,
                    self.client._api.get(
                        path=f"organizations/{self.name}/workspaces/{name}"
                    ),
                )
                self.attrs["workspaces"][ws.id] = ws
            api_response = self.attrs["workspaces"].get(workspace_id)
            return api_response.data
        else:
            raise AttributeError("workspaces")

    def create_workspace(self, **kwargs):
        if self.type == "organizations":
            workspace_model = WorkspaceModel(**kwargs)
            payload = WorkspaceRootModel(
                data=WorkspaceDataModel(type="workspaces", attributes=workspace_model)
            )
            api_response = self.client._api.post(
                path=f"organizations/{self.name}/workspaces", data=payload.json()
            )
            ws = TFCObject(self.client, api_response.data)
            self.attrs["workspaces"][ws.id] = ws
            return ws
        else:
            raise AttributeError("workspaces")

    def create_ssh_key(self, **kwargs):
        if self.type == "organizations":
            model = SshKeyModel(**kwargs)
            payload = SshKeyRootModel(
                data=SshKeyDataModel(type="ssh-keys", attributes=model)
            )
            api_response = self.client._api.post(
                path=f"organizations/{self.name}/ssh-keys", data=payload.json()
            )
            ssh_key = TFCObject(self.client, api_response.data)
            self.attrs["ssh-keys"][ssh_key.id] = ssh_key
            return ssh_key
        else:
            raise AttributeError("workspaces")

    def delete_ssh_key(self, tfc_object):
        if self.type == "organizations":
            id = str(tfc_object)
            if id in self.attrs["ssh-keys"]:
                del self.attrs["ssh-keys"][id]
            return self.client._api.delete(path=f"ssh-keys/{id}")
        else:
            raise AttributeError("delete_workspace")


    def modify(self, **kwargs):
        if self.type in ["workspaces", "vars", "organizations", "ssh-key"]:
            if self.type == "organizations":
                model = OrganizationModel(**kwargs)
                payload = OrganizationRootModel(
                    data=OrganizationDataModel(type="organizations", attributes=model)
                )
                path = f"organizations/{self.name}"

            if self.type == "workspaces":
                model = WorkspaceModel(**kwargs)
                payload = WorkspaceRootModel(
                    data=WorkspaceDataModel(type="workspaces", attributes=model)
                )
                path = f"organizations/{self.organization.id}/workspaces/{self.name}"

            elif self.type == "vars":
                model = VarModel(**kwargs)
                payload = VarRootModel(data=VarDataModel(type="vars", attributes=model))
                path = f"vars/{self.id}"

            elif self.type == "ssh-keys":
                model = SshKeyModel(**kwargs)
                payload = SshKeyRootModel(data=SshKeyDataModel(type="ssh-keys", attributes=model))
                path = f"ssh-keys/{self.id}"

            api_response = self.client._api.patch(path=path, data=payload.json())
            self.refresh()
            # Special case for organizations renaming ...
            # For organization, id == name
            if "id" in api_response.data and api_response.data["id"] != self.id:
                self.id = api_response.data["id"]
            return self
        else:
            raise AttributeError("workspaces")

    def delete_workspace(self, tfc_object):
        if self.type == "organizations":
            id = str(tfc_object)
            if id in self.attrs["workspaces"]:
                del self.attrs["workspaces"][id]
            return self.client._api.delete(path=f"workspaces/{id}")
        else:
            raise AttributeError("delete_workspace")

    def delete_variable(self, tfc_object):
        if self.type == "workspaces":
            id = str(tfc_object)
            if id in self.attrs["vars"]:
                del self.attrs["vars"][id]
            return self.client._api.delete(path=f"vars/{id}")
        else:
            raise AttributeError("delete_variable")

    def do_apply(self, comment=None):
        if self.type == "runs":
            if self.client._api.post(
                path=f"runs/{self.id}/actions/apply",
                json={"comment": comment} if comment else None,
            ):
                self.refresh()
                return True
        else:
            raise AttributeError("do_apply")

    def do_discard(self, comment=None):
        if self.type == "runs":
            if self.client._api.post(
                path=f"runs/{self.id}/actions/discard",
                json={"comment": comment} if comment else None,
            ):
                self.refresh()
                return True
        else:
            raise AttributeError("do_discard")

    def do_cancel(self, comment=None, force=False):
        if self.type == "runs":
            payload_json = {"comment": comment} if comment else None
            if force:
                api_path = f"runs/{self.id}/actions/force-cancel"
            else:
                api_path = f"runs/{self.id}/actions/cancel"

            if self.client._api.post(path=api_path, json=payload_json):
                self.refresh()
                return True
        else:
            raise AttributeError("do_cancel")

    def do_force_execute(self):
        if self.type == "runs":
            if self.client._api.post(path=f"runs/{self.id}/actions/force-execute"):
                self.refresh()
                return True
        else:
            raise AttributeError("do_cancel")

    def do_lock(self):
        if self.type == "workspaces":
            if self.client._api.post(path=f"workspaces/{self.id}/actions/lock"):
                self.refresh()
                return True
        else:
            raise AttributeError("do_lock")

    def do_unlock(self, force=False):
        if self.type == "workspaces":
            if force:
                api_path = f"workspaces/{self.id}/actions/unlock"
            else:
                api_path = f"workspaces/{self.id}/actions/force-unlock"

            if self.client._api.post(path=api_path):
                self.refresh()
                return True
        else:
            raise AttributeError("do_lock")

    def wait_run(
        self, target_status, sleep_time=3, timeout=600, progress_callback=None
    ):
        if self.type == "runs":
            if not progress_callback or not callable(progress_callback):
                progress_callback = None

            start_time = time.time()
            while True:
                duration = int(time.time() - start_time)
                if RunStatus(self.status) in target_status:
                    return True

                if duration <= timeout:
                    if progress_callback:
                        progress_callback(run=self, duration=duration)
                    time.sleep(sleep_time)
                    self.refresh()
                else:
                    return False
        else:
            raise AttributeError("wait_run")

    def wait_plan(self, sleep_time=3, timeout=600, progress_callback=None):
        if self.type == "runs":
            target_status = [
                RunStatus.planned,
                RunStatus.planned_and_finished,
                RunStatus.errored,
            ]
            return self.wait_run(
                sleep_time=sleep_time,
                timeout=timeout,
                target_status=target_status,
                progress_callback=progress_callback,
            )
        else:
            raise AttributeError("wait_plan")

    def wait_apply(self, sleep_time=3, timeout=600, progress_callback=None):
        if self.type == "runs":
            target_status = [RunStatus.errored, RunStatus.applied]
            return self.wait_run(
                sleep_time=sleep_time,
                timeout=timeout,
                target_status=target_status,
                progress_callback=progress_callback,
            )
        else:
            raise AttributeError("wait_apply")

    def create_run(self, message=None, is_destroy=False):
        if self.type == "workspaces":
            # TODO: Remove this sleep (If create_run is executed too quickly after ws creation: it fail :()
            time.sleep(2)
            if not message:
                message = "Queued manually via the Terraform Enterprise API"

            workspace_data = WorkspaceRootModel(
                data=WorkspaceDataModel(type="workspaces", id=self.id)
            )
            run = RunRootModel(
                data=RunDataModel(
                    type="runs",
                    attributes=RunModel(is_destroy=is_destroy, message=message),
                    relationships=RelationshipsModel(workspace=workspace_data),
                )
            )
            api_response = self.client._api.post(path=f"runs", data=run.json())
            run = TFCObject(self.client, api_response.data)
            self.attrs["runs"][run.id] = run
            return run
        else:
            raise AttributeError("create_run")

    @property
    def log_colored(self):
        if self.type in ["plans", "applies"]:
            if "log" not in self.attrs:
                self.attrs["log"] = self.client._api.get_raw(path=self.log_read_url)
            return self.attrs["log"]
        else:
            raise AttributeError("log_colored")

    @property
    def log(self):
        if self.type in ["plans", "applies"]:
            return re.sub(r"\x1b(\[.*?[@-~]|\].*?(\x07|\x1b\\))", "", self.log_colored)
        else:
            raise AttributeError("log")

    @property
    def log_resume(self):
        if self.type == "plans":
            return "\n".join(
                [
                    line
                    for line in self.log.splitlines()
                    if line.startswith("  + ")
                    or line.startswith("  - ")
                    or line.startswith("-/+ ")
                    or line.startswith("  ~ ")
                ]
            )
        else:
            raise AttributeError("log_resume")

    @property
    def log_changes(self):
        if self.type == "plans":
            return_lines = False
            filtered_log = ""
            for line in self.log.splitlines():
                if re.match("Terraform will perform the following actions", line):
                    return_lines = True
                if return_lines:
                    filtered_log += line + "\n"
            return filtered_log
        else:
            raise AttributeError("log_resume")

    @property
    def log_signature(self):
        if self.type == "plans":
            return hashlib.sha256(bytes(self.log_resume, encoding="utf-8")).hexdigest()
        else:
            raise AttributeError("log_signature")

    def __str__(self):
        return self.id

    def __getattr__(self, key):
        key_dash = InflectionStr(key).dasherize
        if key.startswith("create_"):
            pass
        elif key_dash in self.attributes:
            return self.attributes[key_dash]
        elif self.relationships and key_dash in self.relationships:
            return self.relationships[key_dash]
        else:
            raise AttributeError(key)

class TFCWorkspace(TFCObject):
    type = "workspaces"

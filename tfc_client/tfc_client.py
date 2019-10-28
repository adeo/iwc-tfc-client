from collections.abc import Mapping, Iterable
import time

import inflection

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


class TFCClient(object):
    def __init__(self, token: str, url: str = "https://app.terraform.io"):
        self._token = token
        self._url = url
        self._attrs = dict()

        headers = {
            "Content-Type": "application/vnd.api+json",
            "Authorization": "Bearer {}".format(token),
        }
        self._api = APICaller(host=url, base_url="api/v2", headers=headers)

    def get(self, object_type, id):
        return TFCObject(self, {"type": object_type, "id": id})

    def __getattr__(self, attr):
        if attr.startswith("get_"):
            object_type = inflection.pluralize(inflection.dasherize(attr[4:]))

            def _get_object_type(*args, **kwargs):
                return self.get(
                    object_type, id=kwargs["id"] if "id" in kwargs else args[0]
                )

            return _get_object_type
        else:
            raise AttributeError(attr)

    def create_organization(self, organization_model):
        payload = OrganizationRootModel(
            data=OrganizationDataModel(
                type="organizations", attributes=organization_model
            )
        )
        data, meta, links = self._api.post(path=f"organizations", data=payload.json())
        return TFCObject(self, data)

    def destroy_organization(self, organization_name):
        self._api.delete(path=f"organizations/{organization_name}")


class TFCObject(object):
    def __init__(self, client, data):
        self.client = client
        self.attrs = dict()
        self.attrs["workspaces"] = dict()
        self.attrs["runs"] = dict()
        self.attrs["vars"] = dict()
        self.id = data["id"]
        self.type = data["type"]
        self._init_from_data(data)

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

            data = self.client._api.get_one(path=data_url)
            self._init_from_data(data)

    def refresh(self):
        self.attrs = dict()
        self.attrs["workspaces"] = dict()
        self.attrs["runs"] = dict()
        self.attrs["vars"] = dict()

    @property
    def attributes(self):
        if "attributes" not in self.attrs:
            self._get_data("attributes")
        return self.attrs["attributes"]

    @attributes.setter
    def attributes(self, attributes_dict):
        self.attrs["attributes"] = attributes_dict

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
            if "vars" not in self.attrs:
                organization = self.relationships["organization"]
                self.variables = self.client._api.get_filtered(
                    path="vars", workspace=self.name, organization=organization.name
                )
            return self.attrs["vars"]
        else:
            raise AttributeError("variables")

    @variables.setter
    def variables(self, variables_list):
        if self.type == "workspaces":
            self.attrs["vars"] = dict()
            organization = self.relationships["organization"]
            for var in variables_list:
                var_object = TFCObject(self.client, var)
                self.attrs["vars"][var_object.key] = var_object
        else:
            raise AttributeError("variables")

    def create_variable(
        self, key, value, category="terraform", sensitive=False, hcl=False
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

            data, meta, links = self.client._api.post(path=f"vars", data=payload.json())
            var = TFCObject(self.client, data)
            self.attrs["vars"][var.id] = var
            return var
        else:
            raise AttributeError("variables")

    @property
    def workspaces(self):
        if self.type == "organizations":
            organization = self.name
            for ws in self.client._api.get_paginated(
                path=f"organizations/{organization}/workspaces"
            ):
                ws_id = ws["id"]
                self.attrs["workspaces"][ws_id] = TFCObject(self.client, ws)
                yield self.attrs["workspaces"][ws_id]
        else:
            raise AttributeError("workspaces")

    def workspace(self, *, workspace_id=None, workspace_name=None):
        if self.type == "organizations":
            assert not (
                workspace_id and workspace_name
            ), "You must choose between workspace_id= and workspace_name="
            if workspace_name:
                ws_ids = [
                    ws_id
                    for ws_id, ws in self.attrs["workspaces"].items()
                    if ws.name == workspace_name
                ]
                workspace_id = ws_ids[0]
            elif not workspace_id:
                raise AttributeError("workspace_id or workspace_name must be specified")

            if workspace_id and workspace_id not in self.attrs["workspaces"]:
                ws = TFCObject(
                    self.client,
                    self.client._api.get_one(path=f"workspaces/{workspace_id}"),
                )
                self.attrs["workspaces"][ws.id] = ws
            elif workspace_name and not ws_ids:
                ws = TFCObject(
                    self.client,
                    self.client._api.get_one(
                        path=f"organizations/{self.name}/workspaces/{workspace_name}"
                    ),
                )
                self.attrs["workspaces"][ws.id] = ws
            return self.attrs["workspaces"].get(workspace_id)
        else:
            raise AttributeError("workspaces")

    def create_workspace(self, workspace_model):
        if self.type == "organizations":
            payload = WorkspaceRootModel(
                data=WorkspaceDataModel(type="workspaces", attributes=workspace_model)
            )
            data, meta, links = self.client._api.post(
                path=f"organizations/{self.name}/workspaces", data=payload.json()
            )
            ws = TFCObject(self.client, data)
            self.attrs["workspaces"][ws.id] = ws
            return ws
        else:
            raise AttributeError("workspaces")

    def delete_workspace(self, workspace_id):
        if self.type == "organizations":
            self.client._api.delete(path=f"workspaces/{workspace_id}")
            if workspace_id in self.attrs["workspaces"]:
                del self.attrs["workspaces"][workspace_id]
        else:
            raise AttributeError("delete_workspace")

    def apply(self, comment=None):
        if self.type == "runs":
            self.client._api.post(
                path=f"runs/{self.id}/actions/apply",
                json={"comment": comment} if comment else None,
            )
        else:
            raise AttributeError("apply")

    def wait_run(
        self, sleep_time=3, timeout=600, target_status="planned", progress_callback=None, target_callback=None
    ):
        """target_status can be: planned, applied
        """
        # TODO : Need to define a Enum for target_status
        if self.type == "runs":
            if not progress_callback or not callable(progress_callback):
                progress_callback = None
            if not target_callback or not callable(target_callback):
                target_callback = None

            start_time = time.time()
            while True:
                duration = time.time() - start_time
                if self.status == target_status:
                    if target_callback:
                        target_callback(duration=duration, status=self.status, run=self)
                    break

                if duration <= timeout:
                    if progress_callback:
                        progress_callback(duration=duration, timeout=timeout, status=self.status, run=self)
                    time.sleep(sleep_time)
                    self.refresh()
                else:
                    break

    def create_run(self, message=None, is_destroy=False):
        if self.type == "workspaces":
            # If create_run is executed too quickly after ws creation: it fail :(
            # TODO: Remove this sleep
            time.sleep(2)
            if not message:
                message = "Queued manually via the Terraform Enterprise API"

            payload = {"is-destroy": is_destroy, "message": message}
            workspace_data = {"data": {"type": "workspaces", "id": self.id}}

            run = RunRootModel(
                data=RunDataModel(
                    type="runs",
                    attributes=RunModel(**payload),
                    relationships=RelationshipsModel(
                        workspace=WorkspaceRootModel(**workspace_data)
                    ),
                )
            )
            data, meta, links = self.client._api.post(path=f"runs", data=run.json())
            run = TFCObject(self.client, data)
            self.attrs["runs"][run.id] = run
            return run

    def __getattr__(self, key):
        key_dash = inflection.dasherize(key)
        key_classname = inflection.camelize(key)
        if key.startswith("create_"):
            pass
        elif key_dash in self.attributes:
            return self.attributes[key_dash]
        elif self.relationships and key_dash in self.relationships:
            return self.relationships[key_dash]
        else:
            raise AttributeError(key)

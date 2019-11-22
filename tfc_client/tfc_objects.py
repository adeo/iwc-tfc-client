from collections.abc import Mapping, Iterable
import hashlib
import importlib
import re
import time
from typing import Generator, List, Callable, TYPE_CHECKING

from .models.data import RootModel, DataModel, AssignModel
from .models.run import RunModel
from .models.relationship import RelationshipsModel
from .models.ssh_key import SshKeyModel
from .models.var import VarModel
from .models.workspace import WorkspaceModel
from .tfc_object import TFCObject
from .util import InflectionStr

from .enums import RunStatus, VarCat, WorkspaceSort


if TYPE_CHECKING:
    from .tfc_client import TFCClient

    Mixin = TFCObject
else:
    Mixin = object


class Paginable(Mixin):
    @property
    def pagination(self) -> Mapping:
        if "pagination" not in self.attrs:
            api_response = self.client._api.get(
                path=f"organizations/{self.name}/workspaces", params={"page[size]": 1}
            )
            if "pagination" in api_response.meta:
                self.attrs["pagination"] = api_response.meta["pagination"]
        return self.attrs.get("pagination", {})

    @pagination.setter
    def pagination(self, pagination: Mapping):
        self.attrs["pagination"] = pagination


class Creatable(Mixin):
    def get_list(
        self, object_type: str, filters: str = None, url_prefix: str = None
    ) -> Generator[TFCObject, None, None]:
        object_type = InflectionStr(object_type).dasherize.pluralize
        path_elements = list()
        if url_prefix is not None:
            if url_prefix:
                path_elements.append(url_prefix)
        elif self.url_prefix is not None:
            path_elements.append(self.url_prefix)
        path_elements.append(object_type)
        path = "/".join(path_elements)
        for api_response in self.client._api.get_list(path=path, filters=filters):
            if "pagination" in api_response.meta:
                self.pagination = api_response.meta["pagination"]
            if "status-counts" in api_response.meta:
                self.status_counts = api_response.meta["status-counts"]
            for element in api_response.data:
                tfc_object = self.client.factory(element)
                if tfc_object.type not in self.attrs:
                    self.attrs[tfc_object.type] = dict()
                self.attrs[tfc_object.type][tfc_object.id] = tfc_object
                yield self.attrs[tfc_object.type][tfc_object.id]

    def create(self, object_type: str, url_prefix: str = None, **kwargs) -> TFCObject:
        if self.can_create:
            object_type = InflectionStr(object_type).dasherize.pluralize
            path_elements = list()
            if url_prefix is not None:
                if url_prefix:
                    path_elements.append(url_prefix)
            elif self.url_prefix is not None:
                path_elements.append(self.url_prefix)
            path_elements.append(object_type)
            path = "/".join(path_elements)

            object_class_name = "TFC{type}".format(
                type=InflectionStr(object_type).underscore.camelize.singularize
            )
            if object_type in self.can_create:
                model_class_name = "{type}Model".format(
                    type=InflectionStr(object_type).underscore.camelize.singularize
                )
                module = importlib.import_module(TFCObject.MODELS_MODULE)
                model_class = getattr(module, model_class_name)
                object_attributes = dict()
                relationships = dict()
                for attr_name, attr_value in kwargs.items():
                    if attr_name in model_class.__fields__:
                        object_attributes[attr_name] = attr_value
                    elif isinstance(attr_value, TFCObject):
                        relationships[attr_name] = RootModel(
                            data=DataModel(type=attr_value.type, id=attr_value.id)
                        )

                model = model_class(**object_attributes)
                payload = RootModel(
                    data=DataModel(
                        type=object_type,
                        attributes=model,
                        relationships=RelationshipsModel(**relationships)
                        if relationships
                        else None,
                    )
                )
                api_response = self.client._api.post(path=path, data=payload.json())
                tfc_object = self.client.factory(api_response.data)
                if object_type not in self.attrs:
                    self.attrs[object_type] = dict()
                self.attrs[object_type][tfc_object.id] = tfc_object
                return tfc_object
            else:
                raise AttributeError(f"Can create {object_type} from {self.type}")

    def delete(self, tfc_object: TFCObject):
        id = str(tfc_object)
        if id in self.attrs.get(tfc_object.type, []):
            del self.attrs[tfc_object.type][id]
        return self.client._api.delete(path=f"{tfc_object.type}/{id}")


class Modifiable(Mixin):
    def modify(self, **kwargs) -> TFCObject:
        model_class_name = "{type}Model".format(
            type=InflectionStr(self.type).underscore.camelize.singularize
        )
        module = importlib.import_module(TFCObject.MODELS_MODULE)
        model_class = getattr(module, model_class_name)

        model = model_class(**kwargs)
        payload = RootModel(data=DataModel(type=self.type, attributes=model))
        path = f"{self.type}/{self.id}"

        api_response = self.client._api.patch(path=path, data=payload.json())
        self.refresh()
        # Special case for organizations renaming ...
        # For organization, id == name
        if "id" in api_response.data and api_response.data["id"] != self.id:
            self.id = api_response.data["id"]
        return self


class Assignable(Mixin):
    def assign(self, relation_name: str = None, assigned_object: TFCObject = None):
        if relation_name:
            relation_name = InflectionStr(relation_name).singularize
        else:
            relation_name = InflectionStr(assigned_object.type).singularize
        model = AssignModel(id=assigned_object.id)
        payload = RootModel(data=DataModel(type=self.type, attributes=model))
        path = f"{self.type}/{self.id}/relationships/{relation_name}"
        api_response = self.client._api.patch(path=path, data=payload.json())
        self.refresh()
        return self

    def unassign(self, relation_name: str):
        relation_name = InflectionStr(relation_name).singularize
        model = AssignModel(id=None)
        payload = RootModel(data=DataModel(type=self.type, attributes=model))
        path = f"{self.type}/{self.id}/relationships/{relation_name}"
        api_response = self.client._api.patch(path=path, data=payload.json())
        self.refresh()
        return self


class Loggable(Mixin):
    @property
    def log_colored(self) -> str:
        if "log" not in self.attrs:
            # Remove the first and last control caracter
            self.attrs["log"] = self.client._api.get_raw(path=self.log_read_url)[1:-1]
        return self.attrs["log"]

    @property
    def log(self) -> str:
        return re.sub(r"\x1b(\[.*?[@-~]|\].*?(\x07|\x1b\\))", "", self.log_colored)


class TFCVar(TFCObject, Modifiable):
    type = "vars"


class TFCNotificationConfiguration(TFCObject):
    type = "notification-configurations"

    def do_verify(self) -> bool:
        api_response = self.client._api.post(
            path=f"notification-configurations/{self.id}/actions/verify"
        )
        if api_response.data:
            self._init_from_data(api_response.data)
            return self.delivery_responses
        else:
            return None


class TFCRun(TFCObject):
    type = "runs"

    def wait_run(
        self,
        target_status: List[RunStatus],
        sleep_time=3,
        timeout=600,
        progress_callback: Callable = None,
    ) -> bool:
        if not progress_callback or not callable(progress_callback):
            progress_callback = None

        start_time = time.time()
        while True:
            duration = int(time.time() - start_time)
            if self.status in target_status:
                return True

            if duration <= timeout:
                if progress_callback:
                    progress_callback(run=self, duration=duration)
                time.sleep(sleep_time)
                self.refresh()
            else:
                return False

    def wait_plan(
        self, sleep_time=3, timeout=600, progress_callback: Callable = None
    ) -> bool:
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

    def wait_apply(
        self, sleep_time=3, timeout=600, progress_callback: Callable = None
    ) -> bool:
        target_status = [RunStatus.errored, RunStatus.applied]
        return self.wait_run(
            sleep_time=sleep_time,
            timeout=timeout,
            target_status=target_status,
            progress_callback=progress_callback,
        )

    def do_apply(self, comment: str = None) -> bool:
        if self.client._api.post(
            path=f"runs/{self.id}/actions/apply",
            json={"comment": comment} if comment else None,
        ):
            self.refresh()
            return True

    def do_discard(self, comment: str = None) -> bool:
        if self.client._api.post(
            path=f"runs/{self.id}/actions/discard",
            json={"comment": comment} if comment else None,
        ):
            self.refresh()
            return True

    def do_cancel(self, comment: str = None, force: bool = False) -> bool:
        payload_json = {"comment": comment} if comment else None
        if force:
            api_path = f"runs/{self.id}/actions/force-cancel"
        else:
            api_path = f"runs/{self.id}/actions/cancel"

        if self.client._api.post(path=api_path, json=payload_json):
            self.refresh()
            return True

    def do_force_execute(self) -> bool:
        if self.client._api.post(path=f"runs/{self.id}/actions/force-execute"):
            self.refresh()
            return True


class TFCWorkspace(TFCObject, Paginable, Modifiable, Creatable, Assignable):
    type = "workspaces"
    can_create = ["vars", "runs", "notification-configurations"]

    def get_list(
        self, object_type: str, filters: Mapping = None, url_prefix=None
    ) -> Generator[TFCObject, None, None]:
        if url_prefix is None:
            url_prefix = f"{self.type}/{self.id}"
        return super().get_list(object_type, filters=filters, url_prefix=url_prefix)

    @property
    def vars(self) -> Generator[TFCVar, None, None]:
        filters = {
            "workspace": {"name": self.name},
            "organization": {"name": self.organization.id},
        }
        url_prefix = ""
        return self.get_list("vars", filters=filters, url_prefix=url_prefix)

    @vars.setter
    def vars(self, variables_list: Mapping):
        for data in variables_list:
            var_object = self.client.factory(data)
            if "vars" not in self.attrs:
                self.attrs["vars"] = dict()
            self.attrs["vars"][var_object.key] = var_object

    @property
    def variables(self):
        return {var.key: var for var in self.vars}

    def create(self, object_type: str, url_prefix: str = None, **kwargs) -> TFCObject:
        object_type = InflectionStr(object_type).dasherize.pluralize
        if object_type in ["vars"]:
            if "category" not in kwargs:
                kwargs["category"] = VarCat.terraform
        if object_type in ["runs", "vars"]:
            url_prefix = ""
            kwargs["workspace"] = self
        if object_type in ["notification-configurations"]:
            url_prefix = f"workspaces/{self.id}"
        if object_type in ["runs"]:
            if not kwargs["message"]:
                kwargs["message"] = "Queued manually via the Terraform Enterprise API"
            if "is_destroy" not in kwargs or not isinstance(kwargs["is_destroy"], bool):
                kwargs["is_destroy"] = False

        return super().create(object_type, url_prefix=url_prefix, **kwargs)

    @property
    def runs(self) -> Generator[TFCRun, None, None]:
        return self.get_list("runs")

    def do_lock(self) -> bool:
        if self.client._api.post(path=f"workspaces/{self.id}/actions/lock"):
            self.refresh()
            return True

    def do_unlock(self, force: bool = False) -> bool:
        if force:
            api_path = f"workspaces/{self.id}/actions/unlock"
        else:
            api_path = f"workspaces/{self.id}/actions/force-unlock"

        if self.client._api.post(path=api_path):
            self.refresh()
            return True


class TFCApply(TFCObject, Loggable):
    type = "applies"


class TFCPlan(TFCObject, Loggable):
    type = "plans"

    @property
    def log_resume(self) -> str:
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

    @property
    def log_changes(self) -> str:
        return_lines = False
        filtered_log = ""
        for line in self.log.splitlines():
            if re.match("Terraform will perform the following actions", line):
                return_lines = True
            if return_lines:
                filtered_log += line + "\n"
        return filtered_log

    @property
    def log_signature(self) -> str:
        return hashlib.sha256(bytes(self.log_resume, encoding="utf-8")).hexdigest()


class TFCSshKey(TFCObject, Modifiable):
    type = "ssh-keys"


class TFCEntitlementSet(TFCObject):
    type = "entitlement-sets"


class TFCComment(TFCObject):
    type = "comments"


class TFCOauthToken(TFCObject):
    type = "oauth-token"


class TFCOauthClient(TFCObject):
    type = "oauth-client"


class TFCStateVersion(TFCObject):
    type = "state-versions"


class TFCConfigurationVersion(TFCObject):
    type = "configuration-versions"


class TFCUser(TFCObject):
    type = "users"


class TFCRunEvent(TFCObject):
    type = "run-events"


class TFCOrganization(TFCObject, Paginable, Modifiable, Creatable):
    type = "organizations"
    can_create = ["workspaces", "ssh-keys"]

    def __init__(
        self,
        client: "TFCClient",
        data: Mapping,
        include: str = None,
        init_from_data: bool = True,
    ):
        self.url_prefix = f"organizations/{data['id']}"
        super().__init__(client, data, include, init_from_data)

    @property
    def status_counts(self) -> Mapping:
        if "status-counts" not in self.attrs:
            api_response = self.client._api.get(
                path=f"organizations/{self.name}/workspaces", params={"page[size]": 1}
            )
            if "status-counts" in api_response.meta:
                self.attrs["status-counts"] = api_response.meta["status-counts"]
        return self.attrs.get("status-counts", {})

    @status_counts.setter
    def status_counts(self, status_counts: Mapping):
        self.attrs["status-counts"] = status_counts

    @property
    def workspaces(self) -> Generator[TFCWorkspace, None, None]:
        return self.get_list("workspaces")

    @property
    def ssh_keys(self) -> Generator[TFCSshKey, None, None]:
        return self.get_list("ssh-keys")

    def get(self, *args, **kwargs) -> "TFCObject":
        return self.client.get(*args, **kwargs)

    def workspaces_search(
        self,
        *,
        search: str = None,
        filters: str = None,
        include: str = None,
        sort: WorkspaceSort = None,
        limit: int = None,
    ) -> Generator[TFCWorkspace, None, None]:
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

                if "workspaces" not in self.attrs:
                    self.attrs["workspaces"] = dict()
                self.attrs["workspaces"][ws_id] = self.client.factory(
                    ws, include=included_rel_data if included_rel_data else None
                )

                yield self.attrs["workspaces"][ws_id]
                count += 1

    def workspace(self, name: str) -> TFCWorkspace:
        workspace_id = None
        ws_ids = [
            ws_id for ws_id, ws in self.attrs["workspaces"].items() if ws.name == name
        ]
        if ws_ids:
            workspace_id = ws_ids[0]

        if workspace_id:
            return self.attrs["workspaces"][workspace_id]
        else:
            api_response = self.client._api.get(
                path=f"organizations/{self.name}/workspaces/{name}"
            )
            ws = self.client.factory(api_response.data)
            if "workspaces" not in self.attrs:
                self.attrs["workspaces"] = dict()
            self.attrs["workspaces"][ws.id] = ws
            return ws

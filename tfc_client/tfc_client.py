from collections.abc import Mapping, Iterable
import hashlib
import importlib
import re
import time
from typing import Generator, NoReturn

from .exception import UnmanagedObjectTypeException
from .models.data import DataModel, RootModel
from .models.organization import OrganizationModel
from .util import InflectionStr

from .api_caller import APICaller
from .tfc_object import TFCObject
from .tfc_objects import TFCOrganization


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

    OBJECTS_MODULE = "tfc_client.tfc_objects"

    def __init__(self, token: str, url: str = "https://app.terraform.io"):
        headers = {
            "Content-Type": "application/vnd.api+json",
            "Authorization": "Bearer {}".format(token),
        }
        self._api = APICaller(host=url, base_url="api/v2", headers=headers)

    def get(self, object_type: str, id: str) -> TFCObject:
        object_type = InflectionStr(object_type).dasherize.pluralize
        return self.factory({"type": object_type, "id": id})

    def create_organization(self, **kwargs) -> TFCOrganization:
        organization_model = OrganizationModel(**kwargs)
        payload = RootModel(
            data=DataModel(type="organizations", attributes=organization_model)
        )
        api_response = self._api.post(path=f"organizations", data=payload.json())
        return self.factory(api_response.data)

    def destroy_organization(self, organization_name: str) -> NoReturn:
        self._api.delete(path=f"organizations/{organization_name}")

    @property
    def organizations(self) -> Generator[TFCObject, None, None]:
        for api_response in self._api.get_list(path="organizations"):
            for org_data in api_response.data:
                yield self.factory(org_data)

    def factory(self, data: dict, include: str = None) -> TFCObject:
        if "id" not in data or "type" not in data:
            raise UnmanagedObjectTypeException("No type and/or id in data")
        object_type = InflectionStr(data["type"]).singularize.underscore.camelize
        class_name = "TFC{type}".format(type=object_type)
        module = importlib.import_module(TFCClient.OBJECTS_MODULE)
        try:
            tfc_class = getattr(module, class_name)
            return tfc_class(client=self, data=data, include=include)
        except AttributeError:
            return TFCObject(client=self, data=data, include=include)

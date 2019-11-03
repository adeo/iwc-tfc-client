from collections.abc import Mapping, Iterable
import hashlib
import importlib
import re
import time

from .models.data import DataModel, RootModel
from .models.organization import OrganizationModel
from .util import InflectionStr

from .api_caller import APICaller
from .tfc_object import TFCObject


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
        return self.factory({"type": object_type, "id": id})

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
        payload = RootModel(
            data=DataModel(type="organizations", attributes=organization_model)
        )
        api_response = self._api.post(path=f"organizations", data=payload.json())
        return self.factory(api_response.data)

    def destroy_organization(self, organization_name):
        self._api.delete(path=f"organizations/{organization_name}")

    @property
    def organizations(self):
        for api_response in self._api.get_list(path=f"organizations"):
            for org_data in api_response.data:
                yield self.factory(org_data)

    def factory(self, data, include=None):
        object_type = InflectionStr(data["type"])
        class_name = "TFC{type}".format(
            type=object_type.singularize.underscore.camelize
        )
        module = importlib.import_module("tfc_client.tfc_objects")
        tfc_class = getattr(module, class_name)
        return tfc_class(self, data, include)

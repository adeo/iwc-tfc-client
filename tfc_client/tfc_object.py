from collections.abc import Mapping, Iterable
import importlib
from typing import Any, Dict, Generator, List, NoReturn, Optional, TYPE_CHECKING

from .util import InflectionStr

if TYPE_CHECKING:
    from .tfc_client import TFCClient


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

    MODELS_MODULE = "tfc_client.models"
    can_create = None
    url_prefix = ""

    def __init__(
        self,
        client: "TFCClient",
        data: Mapping,
        include: List[Dict[str, dict]] = None,
        init_from_data=True,
    ):
        self.client = client
        self.attrs: Dict[str, Dict[str, TFCObject]] = dict()
        self.attrs["workspaces"] = dict()
        self.attrs["runs"] = dict()
        self.attrs["vars"] = dict()
        self.attrs["ssh-keys"] = dict()
        self.id = data["id"]
        self.type = data["type"]
        self._model = None

        if init_from_data:
            self._init_from_data(data)

        if include and isinstance(include, Iterable):
            for included_data in include:
                for rel_name, rel in self.relationships.items():
                    if rel.id == included_data["id"]:
                        self.relationships[rel_name] = self.client.factory(
                            included_data
                        )

    def _init_from_data(self, data: Mapping) -> NoReturn:
        if "attributes" in data:
            self.attributes = data["attributes"]
            model_class_name = "{}Model".format(
                InflectionStr(self.type).underscore.singularize.camelize
            )
            module = importlib.import_module(TFCObject.MODELS_MODULE)
            try:
                model_class = getattr(module, model_class_name)
                self._model = model_class(**data["attributes"])
            except AttributeError:
                pass

        if "relationships" in data:
            self.relationships = data["relationships"]

        if "links" in data:
            self.links = data["links"]

    def _get_data(self, object_type) -> NoReturn:
        if object_type not in self.attrs:
            if self.links and "related" in self.links:
                data_url = self.links["related"]
            else:
                data_url = f"{self.type}/{self.id}"

            api_response = self.client._api.get(path=data_url)
            self._init_from_data(api_response.data)

    def refresh(self) -> NoReturn:
        self.attrs = dict()
        self._model = None
        self.attrs["workspaces"] = dict()
        self.attrs["runs"] = dict()
        self.attrs["vars"] = dict()
        self.attrs["ssh-keys"] = dict()

    @property
    def attributes(self) -> Mapping:
        if "attributes" not in self.attrs:
            self._get_data("attributes")
        return self.attrs["attributes"]

    @attributes.setter
    def attributes(self, attributes: Dict[str, Any]):
        self.attrs["attributes"] = attributes

    @property
    def relationships(self) -> Optional[Dict[str, "TFCObject"]]:
        if "relationships" not in self.attrs:
            self._get_data("relationships")
        return self.attrs.get("relationships")

    @relationships.setter
    def relationships(self, relationships: Dict[str, dict]):
        self.attrs["relationships"] = dict()
        for relationship_key, relationship_value in relationships.items():
            if "data" in relationship_value:
                if isinstance(relationship_value["data"], Mapping):
                    self.attrs["relationships"][relationship_key] = self.client.factory(
                        relationship_value["data"]
                    )
                elif isinstance(relationship_value["data"], Iterable):
                    self.attrs["relationships"][relationship_key] = list()
                    for data in relationship_value["data"]:
                        self.attrs["relationships"][relationship_key].append(
                            self.client.factory(data)
                        )

    @property
    def links(self) -> Optional[Dict[str, "TFCObject"]]:
        return self.attrs.get("links")

    @links.setter
    def links(self, links):
        self.attrs["links"] = links

    def __str__(self) -> str:
        return self.id

    def __getattr__(self, key):
        key_dash = InflectionStr(key).dasherize

        if self._model and key in self._model.__fields_set__:
            return getattr(self._model, key)
        elif key_dash in self.attributes:
            return self.attributes[key_dash]
        elif self.relationships and key_dash in self.relationships:
            return self.relationships[key_dash]
        else:
            raise AttributeError(key)

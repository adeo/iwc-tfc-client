from collections.abc import Mapping, Iterable

from .util import InflectionStr


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

    can_create = None
    url_prefix = ""

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
                        self.relationships[rel_name] = self.client.factory(
                            included_data
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
    def links(self):
        return self.attrs.get("links")

    @links.setter
    def links(self, links_dict):
        self.attrs["links"] = links_dict

    def __str__(self):
        return self.id

    def __getattr__(self, key):
        key_dash = InflectionStr(key).dasherize

        if key_dash in self.attributes:
            return self.attributes[key_dash]
        elif self.relationships and key_dash in self.relationships:
            return self.relationships[key_dash]
        else:
            raise AttributeError(key)

from typing import Optional

from . import KebabCaseBaseModel
from .relationship import RelationshipsModel


class SshKeyModel(KebabCaseBaseModel):
    name: Optional[str]
    value: Optional[str]


class SshKeyDataModel(KebabCaseBaseModel):
    type: str = "ssh-keys"
    attributes: SshKeyModel
    relationships: Optional[RelationshipsModel]


class SshKeyRootModel(KebabCaseBaseModel):
    data: SshKeyDataModel

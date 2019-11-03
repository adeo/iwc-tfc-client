from typing import Optional

from . import KebabCaseBaseModel
from .data import AttributesModel
from .relationship import RelationshipsModel


class SshKeyModel(AttributesModel):
    name: Optional[str]
    value: Optional[str]

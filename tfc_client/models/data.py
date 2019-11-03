from typing import Optional

from . import KebabCaseBaseModel
from .relationship import RelationshipsModel


class AttributesModel(KebabCaseBaseModel):
    pass


class DataModel(KebabCaseBaseModel):
    id: Optional[str]
    type: str
    attributes: Optional[AttributesModel]
    relationships: Optional[RelationshipsModel]


class RootModel(KebabCaseBaseModel):
    data: DataModel

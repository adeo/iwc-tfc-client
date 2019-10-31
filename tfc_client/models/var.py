from typing import Optional, List
from . import KebabCaseBaseModel
from .relationship import RelationshipsModel

from ..enums import VarCat


class VarModel(KebabCaseBaseModel):
    key: Optional[str]
    value: Optional[str]
    category: Optional[VarCat] = VarCat.terraform
    hcl: Optional[bool] = False
    sensitive: Optional[bool] = False


class VarDataModel(KebabCaseBaseModel):
    type: str = "vars"
    attributes: VarModel
    relationships: Optional[RelationshipsModel]


class VarRootModel(KebabCaseBaseModel):
    data: VarDataModel

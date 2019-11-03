from typing import Optional, List
from . import KebabCaseBaseModel
from .data import AttributesModel
from .relationship import RelationshipsModel

from ..enums import VarCat


class VarModel(AttributesModel):
    key: Optional[str]
    value: Optional[str]
    category: Optional[VarCat] = VarCat.terraform
    hcl: Optional[bool] = False
    sensitive: Optional[bool] = False

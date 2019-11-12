from typing import Optional, List

from .data import AttributesModel
from ..enums import VarCat


class VarModel(AttributesModel):
    key: Optional[str]
    value: Optional[str]
    category: Optional[VarCat] = VarCat.terraform
    hcl: Optional[bool] = False
    sensitive: Optional[bool] = False

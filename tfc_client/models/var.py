from __future__ import annotations

from typing import Optional, List
from . import KebabCaseModel
from .relationship import RelationshipsModel

class VarModel(KebabCaseModel):
    key: str
    value: str
    category: str = "terrraform" # terrraform or env
    hcl: bool = False
    sensitive: bool = False

class VarDataModel(KebabCaseModel):
    type: str = "vars"
    attributes: VarModel
    relationships: RelationshipsModel

class VarRootModel(KebabCaseModel):
    data: VarDataModel

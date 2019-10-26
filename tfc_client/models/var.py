from __future__ import annotations

from typing import Optional, List
from . import KebabCaseBaseModel
from .relationship import RelationshipsModel


class VarModel(KebabCaseBaseModel):
    key: str
    value: str
    category: str = "terrraform"  # terrraform or env
    hcl: bool = False
    sensitive: bool = False


class VarDataModel(KebabCaseBaseModel):
    type: str = "vars"
    attributes: VarModel
    relationships: RelationshipsModel


class VarRootModel(KebabCaseBaseModel):
    data: VarDataModel

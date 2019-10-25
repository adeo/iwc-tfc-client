from __future__ import annotations

from typing import Optional, List
from . import KebabCaseModel
from .relationship import RelationshipsModel

class RunModel(KebabCaseModel):
    is_destroy: bool = False
    message: str = "Queued manually via the Terraform Enterprise API"

class RunDataModel(KebabCaseModel):
    type: str = "runs"
    attributes: RunModel
    relationships: RelationshipsModel

class RunRootModel(KebabCaseModel):
    data: RunDataModel

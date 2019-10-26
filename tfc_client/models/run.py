from __future__ import annotations

from typing import Optional, List
from . import KebabCaseBaseModel
from .relationship import RelationshipsModel


class RunModel(KebabCaseBaseModel):
    is_destroy: bool = False
    message: str = "Queued manually via the Terraform Enterprise API"


class RunDataModel(KebabCaseBaseModel):
    type: str = "runs"
    attributes: RunModel
    relationships: RelationshipsModel


class RunRootModel(KebabCaseBaseModel):
    data: RunDataModel

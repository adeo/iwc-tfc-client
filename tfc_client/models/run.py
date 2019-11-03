from typing import Optional, List
from . import KebabCaseBaseModel
from .data import AttributesModel
from .relationship import RelationshipsModel


class RunModel(AttributesModel):
    is_destroy: bool = False
    message: str = "Queued manually via the Terraform Enterprise API"

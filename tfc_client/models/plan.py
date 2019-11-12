from datetime import datetime
from typing import Optional, Dict

from pydantic import HttpUrl

from ..enums import RunStatus
from .data import AttributesModel


class PlanModel(AttributesModel):
    has_changes: bool
    resource_additions: int
    resource_changes: int
    resource_destructions: int
    log_read_url: HttpUrl
    status: Optional[RunStatus]
    status_timestamps: Optional[Dict[str, datetime]]

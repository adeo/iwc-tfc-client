from datetime import datetime
from typing import Optional, Dict

from ..enums import RunStatus
from .data import AttributesModel


class RunModel(AttributesModel):
    auto_apply: Optional[bool]
    source: Optional[str]
    has_changes: Optional[bool]
    created_at: Optional[datetime]
    status_timestamps: Optional[Dict[str, datetime]]
    actions: Optional[Dict[str, bool]]
    permissions: Optional[Dict[str, bool]]
    is_destroy: bool = False
    message: str = "Queued manually via the Terraform Enterprise API"
    status: Optional[RunStatus]

from datetime import datetime
from typing import Optional, Dict

try:
    from pydantic import HttpUrl
except ImportError:
    from typing import AnyStr as HttpUrl

from ..enums import RunStatus
from .data import AttributesModel


class ApplyModel(AttributesModel):
    resource_additions: int
    resource_changes: int
    resource_destructions: int
    log_read_url: HttpUrl
    status: Optional[RunStatus]
    status_timestamps: Optional[Dict[str, datetime]]

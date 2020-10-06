
from typing import Dict, List, Optional

from pydantic import HttpUrl

from .data import AttributesModel


class ConfigurationVersionModel(AttributesModel):
    auto_queue_runs: Optional[bool]
    error: Optional[str]
    error_message: Optional[str]
    source: Optional[str]
    status: Optional[str]
    status_timestamps: Optional[Dict]
    upload_url: Optional[HttpUrl]
    changed_files: Optional[List[str]]

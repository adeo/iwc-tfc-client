from datetime import datetime
from typing import Optional, List, Dict

try:
    from pydantic import HttpUrl
except ImportError:
    from typing import AnyStr as HttpUrl

from . import KebabCaseBaseModel
from .data import AttributesModel


class VCSRepoModel(KebabCaseBaseModel):
    branch: Optional[str]
    ingress_submodules: Optional[bool]
    identifier: str
    display_identifier: Optional[str]
    oauth_token_id: Optional[str]
    webhook_url: Optional[HttpUrl]
    default_branch: Optional[bool]


class WorkspaceModel(AttributesModel):
    name: Optional[str]
    created_at: Optional[datetime]
    auto_apply: Optional[bool] = False
    environment: Optional[str]
    locked: Optional[bool]
    queue_all_runs: Optional[bool]
    terraform_version: Optional[str]
    working_directory: Optional[str]
    speculative_enabled: Optional[bool]
    latest_change_at: Optional[datetime]
    operations: Optional[bool]
    vcs_repo: Optional[VCSRepoModel]
    description: Optional[str]
    file_triggers_enabled: Optional[bool]
    trigger_prefixes: Optional[List[str]]
    source: Optional[str]
    source_name: Optional[str]
    source_url: Optional[HttpUrl]
    actions: Optional[Dict[str, bool]]
    permissions: Optional[Dict[str, bool]]

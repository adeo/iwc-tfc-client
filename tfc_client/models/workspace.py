from typing import Optional, List
from . import KebabCaseBaseModel
from .data import AttributesModel


class VCSRepoModel(KebabCaseBaseModel):
    branch: Optional[str]
    ingress_submodules: Optional[bool]
    identifier: str
    display_identifier: Optional[str]
    oauth_token_id: str
    webhook_url: Optional[str]
    default_branch: bool


class WorkspacePermissionsModel(KebabCaseBaseModel):
    can_update: bool
    can_destroy: bool
    can_queue_destroy: bool
    can_queue_run: bool
    can_queue_apply: bool
    can_update_variable: bool
    can_lock: bool
    can_unlock: bool
    can_force_unlock: bool
    can_read_settings: bool


class WorkspaceActionsModel(KebabCaseBaseModel):
    is_destroyable: bool


class WorkspaceModel(AttributesModel):
    name: Optional[str]
    auto_apply: Optional[bool] = False
    environment: Optional[str]
    locked: Optional[bool]
    queue_all_runs: Optional[bool]
    terraform_version: Optional[str]
    working_directory: Optional[str]
    speculative_enabled: Optional[bool]
    latest_change_at: Optional[str]
    operations: Optional[bool]
    vcs_repo: Optional[VCSRepoModel]
    permissions: Optional[WorkspacePermissionsModel]
    actions: Optional[WorkspaceActionsModel]
    description: Optional[str]
    file_triggers_enabled: Optional[bool]
    trigger_prefixes: Optional[List[str]]
    source: Optional[str]
    source_name: Optional[str]
    source_url: Optional[str]

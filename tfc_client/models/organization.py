from typing import Optional
from pydantic import EmailStr

from . import KebabCaseBaseModel
from .data import AttributesModel
from .relationship import RelationshipsModel


class OrganizationPermissionsModel(KebabCaseBaseModel):
    can_update: bool
    can_destroy: bool
    can_create_team: bool
    can_create_workspace: bool
    can_manage_subscription: bool
    can_update_oauth: bool
    can_update_sentinel: bool
    can_update_ssh_keys: bool
    can_update_api_token: bool
    can_traverse: bool
    can_create_workspace_migration: Optional[bool]


class OrganizationModel(AttributesModel):
    name: Optional[str]
    external_id: Optional[str]
    created_at: Optional[str]
    email: Optional[EmailStr]
    session_timeout: Optional[int] = 20160
    session_remember: Optional[int] = 20160
    collaborator_auth_policy: Optional[
        str
    ] = "password"  # "password" or "two_factor_mandatory"
    enterprise_plan: Optional[str]
    plan_expired: Optional[str]
    cost_estimation_enabled: Optional[bool] = False
    permissions: Optional[OrganizationPermissionsModel]
    fair_run_queuing_enabled: Optional[bool]
    saml_enabled: Optional[bool]
    two_factor_conformant: Optional[str]
    preview_request: Optional[bool]


class OrganizationDataModel(KebabCaseBaseModel):
    type: str = "organizations"
    attributes: OrganizationModel


class OrganizationRootModel(KebabCaseBaseModel):
    data: OrganizationDataModel

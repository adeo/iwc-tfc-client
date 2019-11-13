from datetime import datetime
from typing import Optional, Dict

from pydantic import EmailStr

from . import KebabCaseBaseModel
from .data import AttributesModel


class OrganizationModel(AttributesModel):
    name: Optional[str]
    external_id: Optional[str]
    created_at: Optional[datetime]
    email: Optional[EmailStr]
    session_timeout: Optional[int] = 20160
    session_remember: Optional[int] = 20160
    collaborator_auth_policy: Optional[
        str
    ] = "password"  # "password" or "two_factor_mandatory"
    enterprise_plan: Optional[str]
    plan_expired: Optional[str]
    cost_estimation_enabled: Optional[bool] = False
    permissions: Optional[Dict[str, bool]]
    fair_run_queuing_enabled: Optional[bool]
    saml_enabled: Optional[bool]
    two_factor_conformant: Optional[str]
    preview_request: Optional[bool]

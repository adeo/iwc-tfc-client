from __future__ import annotations

from typing import Optional

from . import KebabCaseBaseModel


class VCSRepoModel(KebabCaseBaseModel):
    branch: Optional[str]
    ingress_submodules: Optional[bool]
    identifier: str
    display_identifier: Optional[str]
    oauth_token_id: str
    webhook_url: Optional[str]
    default_branch: bool

from __future__ import annotations

from typing import Optional

from . import KebabCaseModel


class VCSRepoModel(KebabCaseModel):
    branch: str
    ingress_submodules: Optional[bool]
    identifier: str
    display_identifier: Optional[str]
    oauth_token_id: str
    webhook_url: Optional[str]
    default_branch: bool

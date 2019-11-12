from datetime import datetime

from .data import AttributesModel


class OauthTokenModel(AttributesModel):
    created_at: datetime
    service_provider_user: str
    has_ssh_key: bool

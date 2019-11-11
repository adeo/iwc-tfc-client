from typing import Optional, List, Any

from pydantic import HttpUrl

from . import KebabCaseBaseModel
from .data import AttributesModel
from .relationship import RelationshipsModel
from ..enums import NotificationTrigger, NotificationsDestinationType


class NotificationConfigurationModel(AttributesModel):
    enabled: bool = True
    name: str
    url: HttpUrl
    destination_type: NotificationsDestinationType
    token: str
    triggers: List[NotificationTrigger]
    delivery_responses: Optional[List[Any]]
    created_at: Optional[str]
    updated_at: Optional[str]

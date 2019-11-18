from datetime import datetime
from typing import Optional, List, Any, Dict

try:
    from pydantic import HttpUrl
except ImportError:
    from typing import AnyStr as HttpUrl

from . import KebabCaseBaseModel
from .data import AttributesModel
from ..enums import NotificationTrigger, NotificationsDestinationType


class DeliveryResponseModel(KebabCaseBaseModel):
    url: HttpUrl
    body: str
    code: int
    headers: Dict[str, List[str]]
    sent_at: datetime
    successful: bool


class NotificationConfigurationModel(AttributesModel):
    enabled: bool = True
    name: str
    url: HttpUrl
    destination_type: NotificationsDestinationType
    token: Optional[str]
    triggers: List[NotificationTrigger]
    delivery_responses: Optional[List[DeliveryResponseModel]]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

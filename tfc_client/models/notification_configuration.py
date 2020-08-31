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
    enabled: Optional[bool] = True
    name: Optional[str]
    url: Optional[HttpUrl]
    destination_type: Optional[NotificationsDestinationType]
    token: Optional[Optional[str]]
    triggers: Optional[List[NotificationTrigger]]
    delivery_responses: Optional[List[DeliveryResponseModel]]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

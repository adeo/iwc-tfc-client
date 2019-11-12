from typing import Optional

from .data import AttributesModel


class SshKeyModel(AttributesModel):
    name: Optional[str]
    value: Optional[str]

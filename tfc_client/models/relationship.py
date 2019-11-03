from typing import Optional, Any

from . import KebabCaseBaseModel

# from .data import RootModel


class RelationshipsModel(KebabCaseBaseModel):
    # Can't write RootModel here because of circular reference
    workspace: Optional[Any]

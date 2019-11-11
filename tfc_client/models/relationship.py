from typing import Optional, Any

from . import KebabCaseBaseModel


class RelationshipsModel(KebabCaseBaseModel):
    # Can't write RootModel here because of circular reference
    workspace: Optional[Any]

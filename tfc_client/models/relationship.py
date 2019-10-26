from typing import Optional

from . import KebabCaseBaseModel
from .workspace import WorkspaceRootModel


class RelationshipsModel(KebabCaseBaseModel):
    workspace: Optional[WorkspaceRootModel]

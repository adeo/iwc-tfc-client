from typing import Optional

from . import KebabCaseModel
from .workspace import WorkspaceRootModel


class RelationshipsModel(KebabCaseModel):
    workspace: Optional[WorkspaceRootModel]

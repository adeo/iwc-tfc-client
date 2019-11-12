import inflection
from pydantic import BaseModel


class KebabCaseBaseModel(BaseModel):
    class Config:
        alias_generator = inflection.dasherize

    def __init__(self, *args, **kwargs):
        dashed_kwargs = {
            inflection.dasherize(key): value for key, value in kwargs.items()
        }
        super().__init__(*args, **dashed_kwargs)

    def json(self, by_alias=True, exclude_unset=True, *args, **kwargs):
        return super().json(
            *args, by_alias=by_alias, exclude_unset=exclude_unset, **kwargs
        )

    def dict(self, by_alias=True, exclude_unset=True, *args, **kwargs):
        return super().dict(
            *args, by_alias=by_alias, exclude_unset=exclude_unset, **kwargs
        )


from .workspace import WorkspaceModel, VCSRepoModel
from .organization import OrganizationModel
from .var import VarModel
from .run import RunModel
from .data import DataModel
from .ssh_key import SshKeyModel
from .notification_configuration import NotificationConfigurationModel
from .oauth_token import OauthTokenModel

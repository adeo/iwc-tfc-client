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

    def json(self, *, by_alias=True, **kwargs):
        # Manage pydantic<v1.0 compatibility
        # https://pydantic-docs.helpmanual.io/usage/exporting_models/#modeljson
        if "skip_defaults" not in kwargs and "exclude_unset" not in kwargs:
            kwargs["exclude_unset"] = True
        try:
            return super().json(by_alias=by_alias, **kwargs)
        except TypeError:
            if "exclude_unset" in kwargs:
                kwargs["skip_defaults"] = True
                del kwargs["exclude_unset"]
            return super().json(by_alias=by_alias, **kwargs)

    def dict(self, *, by_alias=True, **kwargs):
        # Manage pydantic<v1.0 compatibility
        # https://pydantic-docs.helpmanual.io/usage/exporting_models/#modeldict
        if "skip_defaults" not in kwargs and "exclude_unset" not in kwargs:
            kwargs["exclude_unset"] = True
        try:
            return super().dict(by_alias=by_alias, **kwargs)
        except TypeError:
            if "exclude_unset" in kwargs:
                kwargs["skip_defaults"] = True
                del kwargs["exclude_unset"]
            return super().dict(by_alias=by_alias, **kwargs)


from .workspace import WorkspaceModel, VCSRepoModel
from .organization import OrganizationModel
from .var import VarModel
from .run import RunModel
from .data import DataModel
from .ssh_key import SshKeyModel
from .notification_configuration import NotificationConfigurationModel
from .oauth_token import OauthTokenModel

from pydantic import BaseModel


def underscore_to_dash(string):
    dash = ord("-")
    underscore = ord("_")
    return string.translate({underscore: dash})


class KebabCaseBaseModel(BaseModel):
    class Config:
        alias_generator = underscore_to_dash

    def __init__(self, *args, **kwargs):
        dashed_kwargs = {
            underscore_to_dash(key): value for key, value in kwargs.items()
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

from __future__ import annotations

from pydantic import BaseModel

class KebabCaseModel(BaseModel):

    class Config:

        @classmethod
        def alias_generator(cls, value: str) -> str:
            # if string == "self":
            #     return "self_"
            dash = ord('-')
            underscore = ord('_')
            return value.translate({dash: underscore, underscore: dash})
            # return string.replace("-", "_")

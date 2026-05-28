from typing import Literal, TypeAlias
from pydantic import BaseModel


class ContentPartText(BaseModel):
    type: Literal["text"] = "text"
    text: str


# class ContentPartImage(BaseModel):
#     pass


# class ContentPartAudio(BaseModel):
#     pass


ContentPart: TypeAlias = ContentPartText


class FunctionToolCallParams(BaseModel):
    type: Literal["function"] = "function"
    id: str
    fn_name: str
    fn_arguments: str


ToolCallParams: TypeAlias = FunctionToolCallParams

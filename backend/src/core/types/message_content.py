from typing import Literal, Self, TypeAlias
from pydantic import BaseModel


class ContentPartText(BaseModel):
    type: Literal["text"] = "text"
    text: str

    def to_string(self) -> str:
        return self.text

    def __iadd__(self, rhs: "ContentPartText") -> Self:
        self.text += rhs.text
        return self


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

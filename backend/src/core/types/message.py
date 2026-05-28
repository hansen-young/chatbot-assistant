from datetime import datetime
from typing import Iterable, Literal, TypeAlias, Union

from pydantic import BaseModel, Field
from core.types.message_content import ContentPart, ContentPartText, ToolCallParams


class BaseMessage(BaseModel):
    metadata: dict = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.now)


class AssistantMessage(BaseMessage):
    role: Literal["assistant"] = "assistant"
    content: list[ContentPart] | None
    thoughts: str | None = None
    tool_calls: list[ToolCallParams] | None = None


class DeveloperMessage(BaseMessage):
    role: Literal["developer"] = "developer"
    content: list[ContentPartText]


class SystemMessage(BaseMessage):
    role: Literal["system"] = "system"
    content: list[ContentPartText]


class ToolMessage(BaseMessage):
    role: Literal["tool"] = "tool"
    tool_call_id: str
    content: list[ContentPartText]


class UserMessage(BaseMessage):
    role: Literal["user"] = "user"
    content: list[ContentPart]


Message: TypeAlias = Union[
    AssistantMessage,
    DeveloperMessage,
    SystemMessage,
    ToolMessage,
    UserMessage,
]

Messages: TypeAlias = list[Message]

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from .message import AssistantMessage


class ChatResponseTokenUsage(BaseModel):
    inputs: int | None = None
    outputs: int | None = None
    total: int | None = None


class ChatResponseCostUsage(BaseModel):
    inputs: float | None = None
    outputs: float | None = None
    total: float | None = None


class ChatResponseUsage(BaseModel):
    token: ChatResponseTokenUsage | None = None
    cost: ChatResponseCostUsage | None = None


class ChatResponse(BaseModel):
    finish_reason: str | None = None
    """ stop | tool_calls """

    message: AssistantMessage
    created_at: datetime = Field(default_factory=datetime.now)
    model: str | None = None
    usage: ChatResponseUsage | None = None

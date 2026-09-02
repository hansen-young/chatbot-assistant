from abc import ABC, abstractmethod
from typing import AsyncGenerator, Awaitable, Self

from pydantic import BaseModel, ConfigDict

from core.tools import registry
from core.types import ChatResponse, Messages


class AgentConfig(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    name: str | None = None
    model: str | None = None
    system_prompt: str | None = None
    toolsets: set[str] = set()


class Agent(ABC):
    def __init__(self, config: AgentConfig | None = None):
        self.config = config or AgentConfig()

    @abstractmethod
    def compile(self) -> Self: ...

    @abstractmethod
    def run(self, messages: Messages) -> Awaitable[ChatResponse]: ...

    @abstractmethod
    def run_stream(self, messages: Messages) -> AsyncGenerator[ChatResponse, None]: ...

    async def invoke_tool(self, tool_id: str, kwargs: dict):
        ts = tool_id.split(".", 1)[0]

        if (ts in registry.toolsets) and (ts not in self.config.toolsets):
            return f"Error: Tool call {tool_id} forbidden."

        result, exc = await registry.invoke(tool_id, kwargs)

        return str(exc) if exc else result

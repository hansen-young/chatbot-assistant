from abc import ABC, abstractmethod
from typing import Callable, Self

from pydantic import BaseModel, ConfigDict, Field

from core.tools import Toolset, create_function_tool, function_to_json_schema
from core.types import ChatResponse, Messages


class AgentConfig(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    name: str | None = None
    model: str | None = None
    system_prompt: str | None = None
    toolset: Toolset = Field(default_factory=Toolset)


class Agent(ABC):
    def __init__(self, config: AgentConfig | None = None):
        self.config = config or AgentConfig()

    @abstractmethod
    def compile(self) -> Self: ...

    @abstractmethod
    async def run(self, messages: Messages) -> ChatResponse: ...

    # @abstractmethod
    # def run_async(
    #     self, messages: Messages
    # ) -> AsyncGenerator[ChatResponseChunk, None]: ...

    # --- Decorators --- #
    def tool(self, fn: Callable):
        definition = function_to_json_schema(fn)
        tool = create_function_tool(fn)
        self.config.toolset.add(tool, definition)

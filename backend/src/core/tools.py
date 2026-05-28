import inspect
import json
from abc import ABC, abstractmethod
from typing import Any, Awaitable, Callable, Literal, Required, TypeAlias, TypedDict

from pydantic import TypeAdapter


class Tool(ABC):
    @abstractmethod
    async def invoke(self, *args, **kwargs) -> str: ...


class AsyncFunctionTool(Tool):
    def __init__(self, fn: Callable[..., Awaitable]):
        self.fn = fn

    async def invoke(self, *args, **kwargs):
        result = await self.fn(*args, **kwargs)
        return json.dumps(result)


class FunctionTool(Tool):
    def __init__(self, fn: Callable):
        self.fn = fn

    async def invoke(self, *args, **kwargs):
        result = self.fn(*args, **kwargs)
        return json.dumps(result)


class FunctionToolDefinition(TypedDict, total=False):
    type: Required[Literal["function"]]
    name: Required[str]
    description: str
    input_schema: Required[dict[str, Any]]
    # output_schema: dict[str, Any]  # todo: support output schema in the future


ToolDefinition: TypeAlias = FunctionToolDefinition


class Toolset:
    def __init__(self):
        self.definitions: list[ToolDefinition] = []
        self.tools: dict[str, Tool] = {}

    def add(self, tool: Tool, definition: ToolDefinition):
        if definition["name"] in self.tools:
            raise KeyError(f"Tool {definition['name']} is defined more than once.")

        self.definitions.append(definition)
        self.tools[definition["name"]] = tool

    def empty(self):
        return len(self.definitions) == 0

    def get(self, name: str) -> Tool | None:
        return self.tools.get(name)

    async def invoke(self, name: str, kwargs: dict) -> str:
        if not (tool := self.get(name)):
            return f"Error: Tool '{name}' does not exists."

        try:
            return await tool.invoke(**kwargs)
        except Exception as e:
            return f"Tool '{name}' error: {e}"


def create_function_tool(func: Callable) -> Tool:
    if inspect.iscoroutinefunction(func):
        return AsyncFunctionTool(func)

    elif inspect.isfunction(func):
        return FunctionTool(func)

    raise ValueError(f"Unsupported function tool with type {type(func)}")


def function_to_json_schema(func: Callable) -> FunctionToolDefinition:
    name = func.__name__
    description = inspect.getdoc(func) or ""

    return {
        "type": "function",
        "name": name,
        "description": description,
        "input_schema": TypeAdapter(func).json_schema(),
    }

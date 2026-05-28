import json
from datetime import datetime
from typing import cast

from ollama import (
    AsyncClient,
    ChatResponse as OllamaChatResponse,
    Message as OllamaMessage,
    Tool as OllamaTool,
)

from core.tools import ToolDefinition
from core.types.chat import ChatResponse, ChatResponseTokenUsage, ChatResponseUsage
from core.types.message import AssistantMessage, Message, Messages, SystemMessage
from core.types.message_content import (
    ContentPart,
    ContentPartText,
    FunctionToolCallParams,
    ToolCallParams,
)
from .base import Agent, AgentConfig


def adapt_chat_response(response: OllamaChatResponse) -> ChatResponse:
    if response.created_at:
        created_at = datetime.fromisoformat(response.created_at)
    else:
        created_at = datetime.now()

    message = adapt_response_message(response.message)

    if message.tool_calls:
        finish_reason = "tool_calls"
    else:
        finish_reason = "stop"

    return ChatResponse(
        finish_reason=finish_reason,
        created_at=created_at,
        model=response.model,
        usage=ChatResponseUsage(
            token=ChatResponseTokenUsage(
                inputs=response.prompt_eval_count,
                outputs=response.eval_count,
            )
        ),
        message=message,
    )


def adapt_tool_call(i: int, p: OllamaMessage.ToolCall) -> ToolCallParams:
    return FunctionToolCallParams(
        id=str(i),
        fn_name=p.function.name,
        fn_arguments=json.dumps(p.function.arguments),
    )


def adapt_response_message(message: OllamaMessage) -> AssistantMessage:
    content: list[ContentPart] = []
    thoughts: str | None = message.thinking
    tool_calls: list[ToolCallParams] | None = None

    if message.content:
        content.append(ContentPartText(text=message.content))

    if message.tool_calls:
        tool_calls = [adapt_tool_call(i, t) for i, t in enumerate(message.tool_calls)]

    return AssistantMessage(content=content, thoughts=thoughts, tool_calls=tool_calls)


def to_ollama_message(message: Message) -> OllamaMessage:
    ollama_content = ""
    tool_calls: list[OllamaMessage.ToolCall] | None = None

    for content in message.content or []:
        if content.type == "text":
            ollama_content += content.text

    if isinstance(message, AssistantMessage):
        if message.tool_calls:
            tool_calls = [to_ollama_tool_call(p) for p in message.tool_calls]

        return OllamaMessage(
            role=message.role,
            content=ollama_content,
            thinking=message.thoughts,
            tool_calls=tool_calls,
        )

    return OllamaMessage(role=message.role, content=ollama_content)


def to_ollama_tools(definitions: list[ToolDefinition]) -> list[OllamaTool]:
    ollama_tools: list[OllamaTool] = []

    for definition in definitions:
        if definition["type"] == "function":
            ollama_tools.append(
                OllamaTool(
                    **{
                        "type": definition["type"],
                        "function": {
                            "name": definition["name"],
                            "description": definition.get("description"),
                            "parameters": definition["input_schema"],
                        },
                    }
                )
            )

    return ollama_tools


def to_ollama_tool_call(p: ToolCallParams) -> OllamaMessage.ToolCall:
    return OllamaMessage.ToolCall(
        function=OllamaMessage.ToolCall.Function(
            name=p.fn_name,
            arguments=json.loads(p.fn_arguments),
        )
    )


class OllamaAgent(Agent):
    def __init__(self, client: AsyncClient, config: AgentConfig | None = None):
        super().__init__(config)
        self.client = client
        self.ollama_tools: list[OllamaTool] | None = None

    def compile(self):
        self.ollama_tools = to_ollama_tools(self.config.toolset.definitions)
        return self

    async def run(self, messages: Messages):
        if self.config.system_prompt:
            messages = [
                SystemMessage(
                    content=[ContentPartText(text=self.config.system_prompt)]
                ),
                *messages,
            ]

        model: str = cast(str, self.config.model)
        ollama_messages = [to_ollama_message(message) for message in messages]
        response = await self.client.chat(
            model=model, messages=ollama_messages, tools=self.ollama_tools
        )

        return adapt_chat_response(response)

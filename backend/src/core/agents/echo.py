from itertools import batched
from typing import Self

from core.types.chat import ChatResponse, ChatResponseCostUsage, ChatResponseUsage
from core.types.message import AssistantMessage, Messages
from core.types.message_content import ContentPartText
from .base import Agent


class EchoAgent(Agent):
    def compile(self) -> Self:
        return self

    async def run(self, messages: Messages) -> ChatResponse:
        if not messages:
            raise RuntimeError("No messages provided to the agent")

        if messages[-1].role != "user":
            raise RuntimeError("The last message must be from the user")

        reply_content = "Nothing to echo!"

        for content in messages[-1].content:
            if content.type == "text":
                reply_content = "Echo: " + content.text

        return ChatResponse(
            finish_reason="stop",
            message=AssistantMessage(content=[ContentPartText(text=reply_content)]),
            model="echo-agent",
            usage=ChatResponseUsage(cost=ChatResponseCostUsage(total=0)),
        )

    async def run_stream(self, messages: Messages):
        if not messages:
            raise RuntimeError("No messages provided to the agent")

        if messages[-1].role != "user":
            raise RuntimeError("The last message must be from the user")

        reply_content = "Nothing to echo!"

        for content in messages[-1].content:
            if content.type == "text":
                reply_content = "Echo: " + content.text

        chunks = list(batched(reply_content, n=2))

        for i, chunk in enumerate(chunks):
            finish_reason = "stop" if i == len(chunks) - 1 else None
            yield ChatResponse(
                finish_reason=finish_reason,
                message=AssistantMessage(
                    content=[ContentPartText(text="".join(chunk))]
                ),
                model="echo-agent",
                usage=ChatResponseUsage(cost=ChatResponseCostUsage(total=0)),
            )

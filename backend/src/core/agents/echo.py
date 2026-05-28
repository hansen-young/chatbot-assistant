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

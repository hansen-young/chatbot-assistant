import json
from abc import ABC, abstractmethod
from typing import AsyncGenerator, Generator, cast

from core.agents import Agent
from core.sessions import Session, SessionService
from core.types.message import AssistantMessage, ToolMessage, UserMessage
from core.types.message_content import ContentPart


class Runner(ABC):
    def __init__(self, agent: Agent, session_service: SessionService):
        self.agent = agent.compile()
        self.session_service = session_service

    @abstractmethod
    async def run(self, session_id: str, message: str) -> list[ContentPart]: ...

    @abstractmethod
    def run_stream(self, session_id: str, message: str) -> AsyncGenerator: ...


class SimpleRunner(Runner):
    async def _handle_stop_reason(self, session: Session, message: AssistantMessage):
        if not message.content:
            raise RuntimeError("Agent response is empty")
        session.messages.append(message)

    async def _handle_tool_calls_reason(self, session: Session, message: AssistantMessage):  # fmt: skip
        if not message.tool_calls:
            raise RuntimeError("Tool calls information is missing in the response")
        session.messages.append(message)

        for tool_call in message.tool_calls:
            name = tool_call.fn_name
            kwargs: dict = json.loads(tool_call.fn_arguments)
            tool_result = await self.agent.config.toolset.invoke(name, kwargs)
            session.add_message(
                ToolMessage,
                text=tool_result,
                tool_call_id=tool_call.id,
            )

    def handoff_condition(self, session: Session) -> bool:
        return bool(session.messages) and session.messages[-1].role == "assistant"

    async def run(self, session_id: str, message: str) -> list[ContentPart]:
        if not (session := await self.session_service.load(session_id)):
            session = await self.session_service.create(session_id)

        session.add_message(UserMessage, text=message)

        while not self.handoff_condition(session):
            response = await self.agent.run(session.messages)

            if response.finish_reason == "stop":
                await self._handle_stop_reason(session, response.message)
            elif response.finish_reason == "tool_calls":
                await self._handle_tool_calls_reason(session, response.message)
            else:
                raise RuntimeError(f"Unknown finish reason: {response.finish_reason}")

        if not session.messages[-1].content:
            raise RuntimeError("No valid assistant response found")

        await self.session_service.save(session)

        return session.messages[-1].content

    async def run_stream(self, session_id: str, message: str):
        pass

    # async def run_stream(self, session_id: str, message: str):
    #     if not (session := await self.session_service.load(session_id)):
    #         session = await self.session_service.create(session_id)

    #     session.add_message("user", message)
    #     aggregator = ChoiceAggregator()

    #     while not self.handoff_condition(session):
    #         aggregator.reset()

    #         async for chunk in self.agent.run_async(session.messages):
    #             if not chunk.choices:
    #                 continue

    #             choice = chunk.choices[0]
    #             aggregator.update(choice)

    #             if aggregator.choice.message.role == "assistant":
    #                 # todo: if tool_calls is not None, content might be the LLM thought process, we might not want
    #                 #       to yield it directly.
    #                 if choice.delta.content:
    #                     yield choice.delta.content

    #         if aggregator:
    #             session.add_message(
    #                 aggregator.choice.message.role,
    #                 aggregator.choice.message.content,
    #                 tool_calls=aggregator.choice.message.tool_calls,
    #             )

    #             for tc in aggregator.choice.message.tool_calls or []:
    #                 await self._invoke_tool(session, tc)

    #         else:
    #             raise RuntimeError(
    #                 "Invalid response from agent: no content or tool calls"
    #             )

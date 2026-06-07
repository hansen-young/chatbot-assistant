from uuid import uuid4
from typing import Annotated, AsyncIterable

from fastapi import Depends, Header
from fastapi.responses import JSONResponse
from fastapi.routing import APIRouter
from fastapi.sse import EventSourceResponse, ServerSentEvent
from pydantic import BaseModel

from bot import get_runner
from core import context as ctx
from core.runners import Runner
from core.types.message_content import ContentPart

V1Router = APIRouter(prefix="/api/v1", tags=["v1"])

# --- Utils --- #


def stringify(contents: list[ContentPart]) -> str:
    result: str = ""

    for content in contents:
        if content.type == "text":
            result += content.text

    return result


async def set_session_ctx(x_session_id: Annotated[str | None, Header()] = None):
    x_session_id = x_session_id or str(uuid4())
    token = None

    try:
        token = ctx.session_id.set(x_session_id)
        yield x_session_id
    finally:
        if token:
            ctx.session_id.reset(token)


# --- Schema --- #


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    session_id: str
    message: str


# --- Routes --- #


@V1Router.post("/chat", tags=["chat"])
async def chat(
    body: ChatRequest,
    runner: Annotated[Runner, Depends(get_runner)],
    session_id: Annotated[str, Depends(set_session_ctx)],
) -> ChatResponse:
    contents = await runner.run(session_id=session_id, message=body.message)
    return ChatResponse(session_id=session_id, message=stringify(contents))


@V1Router.post("/chat/stream", tags=["chat"], response_class=EventSourceResponse)
async def chat_stream(
    body: ChatRequest,
    runner: Annotated[Runner, Depends(get_runner)],
    session_id: Annotated[str, Depends(set_session_ctx)],
) -> AsyncIterable[ServerSentEvent]:
    async for event in runner.run_stream(session_id=session_id, message=body.message):
        yield event


@V1Router.get("/session/{session_id}", tags=["session"])
async def get_session(session_id: str, runner: Annotated[Runner, Depends(get_runner)]):
    if session := await runner.session_service.load(session_id):
        return session
    return JSONResponse(
        status_code=404,
        content={"detail": f"Session {session_id} not found"},
    )

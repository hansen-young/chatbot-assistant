import json
from uuid import uuid4
from typing import Annotated

from fastapi import Depends, Header
from fastapi.responses import JSONResponse
from fastapi.routing import APIRouter
from fastapi.sse import EventSourceResponse, ServerSentEvent
from pydantic import BaseModel, Field

from bot import get_runner
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
    x_session_id: Annotated[str | None, Header()] = None,
):
    x_session_id = x_session_id or str(uuid4())
    contents = await runner.run(session_id=x_session_id, message=body.message)
    return ChatResponse(session_id=x_session_id, message=stringify(contents))


# @V1Router.post("/chat/stream", tags=["chat"], response_class=EventSourceResponse)
# async def chat_stream(
#     body: ChatRequest, runner: Annotated[Runner, Depends(get_runner)]
# ):
#     async for chunk in runner.run_stream(
#         session_id=body.session_id, message=body.message
#     ):
#         yield chunk

#     yield ServerSentEvent(
#         data=json.dumps({"session_id": body.session_id}),
#         event="end",
#     )


@V1Router.get("/session/{session_id}", tags=["session"])
async def get_session(
    x_session_id: Annotated[str, Header()],
    runner: Annotated[Runner, Depends(get_runner)],
):
    if session := await runner.session_service.load(x_session_id):
        return session
    return JSONResponse(
        status_code=404,
        content={"detail": f"Session {x_session_id} not found"},
    )

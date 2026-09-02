from datetime import datetime
from typing import TypeAlias

from fastapi import Request, HTTPException
from fastapi.routing import APIRouter
from pydantic import BaseModel

from core.tools import ToolDefinition, registry

ToolRouter = APIRouter(prefix="/tools", tags=["tools"])


# --- Schema --- #


class ToolInvokeRequest(BaseModel):
    tool_id: str
    kwargs: dict


class ToolInvokeResponse(ToolInvokeRequest):
    data: str | None
    error: str | None
    timestamp: datetime


ToolListResponse: TypeAlias = dict[str, list[ToolDefinition]]


# --- Routes --- #


@ToolRouter.get("", summary="List all registered tools")
async def list() -> ToolListResponse:
    return {group: toolset.definitions for group, toolset in registry.toolsets.items()}


@ToolRouter.post("/invoke")
async def invoke(body: ToolInvokeRequest):
    result, exc = await registry.invoke(body.tool_id, body.kwargs)

    return ToolInvokeResponse(
        tool_id=body.tool_id,
        kwargs=body.kwargs,
        data=result or None,
        error=str(exc) if exc else None,
        timestamp=datetime.now(),
    )

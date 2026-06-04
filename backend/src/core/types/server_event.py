from typing import TypeAlias, TypedDict

from fastapi.sse import ServerSentEvent


class DeltaMessageSSE(ServerSentEvent):
    class DataType(TypedDict):
        content: str

    event: str | None = "delta"
    data: DataType | None = None


class EndSSE(ServerSentEvent):
    class DataType(TypedDict):
        session_id: str | None

    event: str | None = "end"
    data: DataType | None = None


ChatSSE: TypeAlias = DeltaMessageSSE | EndSSE

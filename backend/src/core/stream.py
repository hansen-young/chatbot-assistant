from core.types.chat import ChatResponse
from core.types.message import AssistantMessage


class ResponseNotReady(Exception): ...


class StreamResponseAggregator:
    def __init__(self):
        self._response = ChatResponse(message=AssistantMessage(content=[]))

    def response(self):
        if self._response.finish_reason is None:
            raise ResponseNotReady("Response is not finished.")
        return self._response

    def _update_message_delta(self, rhs: AssistantMessage):
        lhs = self._response.message

        lhs.metadata.update(rhs.metadata)
        lhs.timestamp = rhs.timestamp

        for content in rhs.content or []:
            lhs.content = lhs.content or []

            if lhs.content == [] or type(content) != type(lhs.content[-1]):
                lhs.content.append(content)
            else:
                lhs.content[-1] += content

        if rhs.thoughts:
            lhs.thoughts = (lhs.thoughts or "") + rhs.thoughts

        # todo: update tool call

    def update(self, chunk: ChatResponse):
        if chunk.message.role != "assistant":
            return

        if chunk.finish_reason:
            self._response.finish_reason = chunk.finish_reason

        if chunk.created_at:
            self._response.created_at = chunk.created_at

        if chunk.model:
            self._response.model = chunk.model

        if chunk.usage:
            self._response.usage = chunk.usage

        self._update_message_delta(chunk.message)

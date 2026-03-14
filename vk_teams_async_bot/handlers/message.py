"""Handler for new message events."""

from __future__ import annotations

from ..types.event import BaseEvent, NewMessageEvent
from .base import BaseHandler


class MessageHandler(BaseHandler):
    """Handler that only processes NewMessageEvent events."""

    def check(self, event: BaseEvent) -> bool:
        return isinstance(event, NewMessageEvent) and super().check(event)

    async def check_async(self, event: BaseEvent) -> bool:
        return isinstance(event, NewMessageEvent) and await super().check_async(event)

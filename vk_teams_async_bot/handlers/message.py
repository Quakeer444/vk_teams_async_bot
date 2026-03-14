"""Handler for new message events."""

from __future__ import annotations

from ..types.event import BaseEvent, NewMessageEvent
from .base import BaseHandler


class MessageHandler(BaseHandler):
    """Handler that only processes NewMessageEvent events."""

    def check(self, event: BaseEvent) -> bool:
        return super().check(event) and isinstance(event, NewMessageEvent)

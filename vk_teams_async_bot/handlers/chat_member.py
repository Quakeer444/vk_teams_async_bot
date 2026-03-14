"""Handlers for chat member events (join/leave)."""

from __future__ import annotations

from ..types.event import BaseEvent, LeftChatMembersEvent, NewChatMembersEvent
from .base import BaseHandler


class NewChatMembersHandler(BaseHandler):
    """Handler that only processes NewChatMembersEvent events."""

    def check(self, event: BaseEvent) -> bool:
        return super().check(event) and isinstance(event, NewChatMembersEvent)


class LeftChatMembersHandler(BaseHandler):
    """Handler that only processes LeftChatMembersEvent events."""

    def check(self, event: BaseEvent) -> bool:
        return super().check(event) and isinstance(event, LeftChatMembersEvent)

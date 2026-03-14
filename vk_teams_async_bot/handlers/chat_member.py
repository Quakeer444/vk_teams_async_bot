"""Handlers for chat member events (join/leave)."""

from __future__ import annotations

from ..types.event import BaseEvent, LeftChatMembersEvent, NewChatMembersEvent
from .base import BaseHandler


class NewChatMembersHandler(BaseHandler):
    """Handler that only processes NewChatMembersEvent events."""

    def check(self, event: BaseEvent) -> bool:
        return isinstance(event, NewChatMembersEvent) and super().check(event)

    async def check_async(self, event: BaseEvent) -> bool:
        return isinstance(event, NewChatMembersEvent) and await super().check_async(event)


class LeftChatMembersHandler(BaseHandler):
    """Handler that only processes LeftChatMembersEvent events."""

    def check(self, event: BaseEvent) -> bool:
        return isinstance(event, LeftChatMembersEvent) and super().check(event)

    async def check_async(self, event: BaseEvent) -> bool:
        return isinstance(event, LeftChatMembersEvent) and await super().check_async(event)

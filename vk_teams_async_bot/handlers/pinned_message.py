"""Handlers for pinned/unpinned message events."""

from __future__ import annotations

from ..types.event import BaseEvent, PinnedMessageEvent, UnpinnedMessageEvent
from .base import BaseHandler


class PinnedMessageHandler(BaseHandler):
    """Handler that only processes PinnedMessageEvent events."""

    def check(self, event: BaseEvent) -> bool:
        return isinstance(event, PinnedMessageEvent) and super().check(event)

    async def check_async(self, event: BaseEvent) -> bool:
        return isinstance(event, PinnedMessageEvent) and await super().check_async(event)


class UnpinnedMessageHandler(BaseHandler):
    """Handler that only processes UnpinnedMessageEvent events."""

    def check(self, event: BaseEvent) -> bool:
        return isinstance(event, UnpinnedMessageEvent) and super().check(event)

    async def check_async(self, event: BaseEvent) -> bool:
        return isinstance(event, UnpinnedMessageEvent) and await super().check_async(event)

"""Handlers for pinned/unpinned message events."""

from __future__ import annotations

from ..types.event import BaseEvent, PinnedMessageEvent, UnpinnedMessageEvent
from .base import BaseHandler


class PinnedMessageHandler(BaseHandler):
    """Handler that only processes PinnedMessageEvent events."""

    def check(self, event: BaseEvent) -> bool:
        return super().check(event) and isinstance(event, PinnedMessageEvent)


class UnpinnedMessageHandler(BaseHandler):
    """Handler that only processes UnpinnedMessageEvent events."""

    def check(self, event: BaseEvent) -> bool:
        return super().check(event) and isinstance(event, UnpinnedMessageEvent)

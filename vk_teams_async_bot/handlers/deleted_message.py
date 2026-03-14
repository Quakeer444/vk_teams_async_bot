"""Handler for deleted message events."""

from __future__ import annotations

from ..types.event import BaseEvent, DeletedMessageEvent
from .base import BaseHandler


class DeletedMessageHandler(BaseHandler):
    """Handler that only processes DeletedMessageEvent events."""

    def check(self, event: BaseEvent) -> bool:
        return isinstance(event, DeletedMessageEvent) and super().check(event)

    async def check_async(self, event: BaseEvent) -> bool:
        return isinstance(event, DeletedMessageEvent) and await super().check_async(event)

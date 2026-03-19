"""Handler for edited message events."""

from __future__ import annotations

from ..types.event import BaseEvent, EditedMessageEvent
from .base import BaseHandler


class EditedMessageHandler(BaseHandler):
    """Handler that only processes EditedMessageEvent events."""

    def check(self, event: BaseEvent) -> bool:
        return isinstance(event, EditedMessageEvent) and super().check(event)

    async def check_async(self, event: BaseEvent) -> bool:
        return isinstance(event, EditedMessageEvent) and await super().check_async(
            event
        )

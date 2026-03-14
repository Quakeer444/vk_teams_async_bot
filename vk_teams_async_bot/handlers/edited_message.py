"""Handler for edited message events."""

from __future__ import annotations

from ..types.event import BaseEvent, EditedMessageEvent
from .base import BaseHandler


class EditedMessageHandler(BaseHandler):
    """Handler that only processes EditedMessageEvent events."""

    def check(self, event: BaseEvent) -> bool:
        return super().check(event) and isinstance(event, EditedMessageEvent)

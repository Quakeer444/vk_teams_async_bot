"""Handler for deleted message events."""

from __future__ import annotations

from ..types.event import BaseEvent, DeletedMessageEvent
from .base import BaseHandler


class DeletedMessageHandler(BaseHandler):
    """Handler that only processes DeletedMessageEvent events."""

    def check(self, event: BaseEvent) -> bool:
        return super().check(event) and isinstance(event, DeletedMessageEvent)

"""Handler for callback query events (inline button presses)."""

from __future__ import annotations

from ..types.event import BaseEvent, CallbackQueryEvent
from .base import BaseHandler


class CallbackQueryHandler(BaseHandler):
    """Handler that only processes CallbackQueryEvent events."""

    def check(self, event: BaseEvent) -> bool:
        return super().check(event) and isinstance(event, CallbackQueryEvent)

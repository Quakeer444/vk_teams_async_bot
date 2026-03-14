"""Callback query filters: exact match and regex matching."""

from __future__ import annotations

import re

from ..types.event import BaseEvent, CallbackQueryEvent
from .base import FilterBase


class CallbackDataFilter(FilterBase):
    """Match exact callback data string."""

    def __init__(self, callback_data: str) -> None:
        self.callback_data = callback_data

    def __call__(self, event: BaseEvent) -> bool:
        if not isinstance(event, CallbackQueryEvent):
            return False
        return event.callback_data == self.callback_data

    def __repr__(self) -> str:
        return f"CallbackDataFilter({self.callback_data!r})"


class CallbackDataRegexpFilter(FilterBase):
    """Match callback data against a regular expression."""

    def __init__(self, pattern: str) -> None:
        self.pattern = re.compile(pattern)

    def __call__(self, event: BaseEvent) -> bool:
        if not isinstance(event, CallbackQueryEvent):
            return False
        return bool(self.pattern.search(event.callback_data))

    def __repr__(self) -> str:
        return f"CallbackDataRegexpFilter({self.pattern.pattern!r})"

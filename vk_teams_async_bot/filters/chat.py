"""Chat-related filters: chat type and chat ID matching."""

from __future__ import annotations

from ..types.enums import ChatType
from ..types.event import BaseEvent
from .base import FilterBase


class ChatTypeFilter(FilterBase):
    """Match events by chat type (private/group/channel).

    Works on any event that has a ``chat`` field.
    """

    def __init__(self, chat_types: ChatType | list[ChatType]) -> None:
        if isinstance(chat_types, list):
            self.types = chat_types
        else:
            self.types = [chat_types]

    def __call__(self, event: BaseEvent) -> bool:
        chat = getattr(event, "chat", None)
        if chat is None:
            return False
        return chat.type in self.types

    def __repr__(self) -> str:
        return f"ChatTypeFilter(types={[str(t) for t in self.types]!r})"


class ChatIdFilter(FilterBase):
    """Match events by chat_id.

    Works on any event that has a ``chat`` field.
    Uses frozenset internally for O(1) lookup.
    """

    def __init__(self, chat_ids: str | list[str]) -> None:
        if isinstance(chat_ids, str):
            self._chat_ids = frozenset([chat_ids])
        else:
            self._chat_ids = frozenset(chat_ids)

    def __call__(self, event: BaseEvent) -> bool:
        chat = getattr(event, "chat", None)
        if chat is None:
            return False
        return chat.chat_id in self._chat_ids

    def __repr__(self) -> str:
        return f"ChatIdFilter(chat_ids={sorted(self._chat_ids)!r})"

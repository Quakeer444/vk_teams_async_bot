"""Composite filters that inspect nested message parts."""

from __future__ import annotations

import re

from ..types.event import BaseEvent, NewMessageEvent
from ..types.message import ForwardPart, ReplyPart
from .base import FilterBase


class RegexpTextPartsFilter(FilterBase):
    """Match regex against text in forwarded/replied message parts.

    Iterates over all ForwardPart and ReplyPart parts in the message
    and checks their nested message text against the pattern.
    """

    def __init__(self, pattern: str) -> None:
        self.pattern = re.compile(pattern)

    def __call__(self, event: BaseEvent) -> bool:
        if not isinstance(event, NewMessageEvent):
            return False
        if not event.parts:
            return False
        for part in event.parts:
            if isinstance(part, (ForwardPart, ReplyPart)):
                msg = part.payload.message
                if msg.text and self.pattern.search(msg.text):
                    return True
        return False

    def __repr__(self) -> str:
        return f"RegexpTextPartsFilter({self.pattern.pattern!r})"


class MessageTextPartFromNickFilter(FilterBase):
    """Match messages with forwarded/replied parts from a specific nick.

    In 'any' mode (all_text_parts_from_nick=False): returns True if ANY
    ForwardPart or ReplyPart has a nested message from the specified nick.

    In 'all' mode (all_text_parts_from_nick=True): returns True only if ALL
    ForwardPart and ReplyPart parts have a nested message from the specified nick.
    If there are no such parts, returns False.
    """

    def __init__(self, nick: str, all_text_parts_from_nick: bool = False) -> None:
        self.nick = nick
        self.all_text_parts_from_nick = all_text_parts_from_nick

    def __call__(self, event: BaseEvent) -> bool:
        if not isinstance(event, NewMessageEvent):
            return False
        if not event.parts:
            return False

        relevant_parts = [
            p for p in event.parts if isinstance(p, (ForwardPart, ReplyPart))
        ]

        if not relevant_parts:
            return False

        if self.all_text_parts_from_nick:
            return all(
                p.payload.message.from_.nick == self.nick for p in relevant_parts
            )
        return any(p.payload.message.from_.nick == self.nick for p in relevant_parts)

    def __repr__(self) -> str:
        return (
            f"MessageTextPartFromNickFilter("
            f"nick={self.nick!r}, "
            f"all_text_parts_from_nick={self.all_text_parts_from_nick!r})"
        )

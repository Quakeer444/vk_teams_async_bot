"""Message-related filters: text matching, commands, tags."""

from __future__ import annotations

import re

from ..types.event import BaseEvent, NewMessageEvent
from .base import FilterBase


class MessageFilter(FilterBase):
    """Matches any NewMessageEvent."""

    def __call__(self, event: BaseEvent) -> bool:
        return isinstance(event, NewMessageEvent)

    def __repr__(self) -> str:
        return "MessageFilter()"


class TextFilter(FilterBase):
    """Match NewMessageEvent that has non-empty, non-whitespace text."""

    def __call__(self, event: BaseEvent) -> bool:
        if not isinstance(event, NewMessageEvent):
            return False
        return bool(event.text and event.text.strip())

    def __repr__(self) -> str:
        return "TextFilter()"


class RegexpFilter(FilterBase):
    """Match message text against a regular expression."""

    def __init__(self, pattern: str) -> None:
        self.pattern = re.compile(pattern)

    def __call__(self, event: BaseEvent) -> bool:
        if not isinstance(event, NewMessageEvent):
            return False
        if event.text is None:
            return False
        return bool(self.pattern.search(event.text))

    def __repr__(self) -> str:
        return f"RegexpFilter({self.pattern.pattern!r})"


class CommandFilter(FilterBase):
    """Match /command messages.

    Extracts the first word from the message text and compares it
    against the expected command (without prefix). For example,
    CommandFilter("start") matches "/start" and "/start arg1 arg2".
    """

    COMMAND_PREFIXES = "/"

    def __init__(self, command: str) -> None:
        self.command = command.lstrip("/")

    def __call__(self, event: BaseEvent) -> bool:
        if not isinstance(event, NewMessageEvent):
            return False
        if not event.text:
            return False
        text = event.text.strip()
        if not any(text.startswith(p) for p in self.COMMAND_PREFIXES):
            return False
        # Extract command: first word without prefix
        first_word = text.split()[0]
        extracted_command = first_word[1:]  # strip the "/" prefix
        return extracted_command == self.command

    def __repr__(self) -> str:
        return f"CommandFilter({self.command!r})"


class TagFilter(FilterBase):
    """Match message text against a list of exact tags."""

    def __init__(self, tags: list[str]) -> None:
        self.tags = tags

    def __call__(self, event: BaseEvent) -> bool:
        if not isinstance(event, NewMessageEvent):
            return False
        return event.text is not None and event.text in self.tags

    def __repr__(self) -> str:
        return f"TagFilter({self.tags!r})"

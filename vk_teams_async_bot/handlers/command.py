"""Handler for command messages (e.g. /start, /help)."""

from __future__ import annotations

from typing import Any, Callable, Sequence

from ..filters.base import FilterBase
from ..filters.message import CommandFilter
from .message import MessageHandler


class CommandHandler(MessageHandler):
    """Handler that matches /command messages.

    If no filters are provided and a command is specified,
    a CommandFilter is automatically created.
    """

    def __init__(
        self,
        callback: Callable[..., Any],
        command: str | None = None,
        filters: FilterBase | Sequence[FilterBase] | None = None,
    ) -> None:
        if filters is None and command is not None:
            filters = CommandFilter(command)
        super().__init__(callback=callback, filters=filters)
        self.command = command

"""Base middleware protocol for the VK Teams bot dispatcher."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Awaitable, Callable

from ..types.event import BaseEvent, RawUnknownEvent

Event = BaseEvent | RawUnknownEvent
HandlerType = Callable[[Event, dict[str, Any]], Awaitable[Any]]


class BaseMiddleware(ABC):
    """Abstract middleware that wraps event processing.

    Each middleware receives the next handler in the chain and can
    decide whether to call it, modify the event/data, or short-circuit.

    Usage::

        class LoggingMiddleware(BaseMiddleware):
            async def __call__(self, handler, event, data):
                print(f"Before: {event.type}")
                result = await handler(event, data)
                print(f"After: {event.type}")
                return result
    """

    @abstractmethod
    async def __call__(
        self,
        handler: HandlerType,
        event: Event,
        data: dict[str, Any],
    ) -> Any:
        """Process the event.

        Args:
            handler: The next handler/middleware in the chain.
            event: The incoming event.
            data: Shared data dict (bot, dispatcher, fsm_context, etc.).

        Returns:
            The result of calling ``handler(event, data)`` or a short-circuit value.
        """
        ...

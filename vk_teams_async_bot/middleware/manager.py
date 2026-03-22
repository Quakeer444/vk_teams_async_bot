"""Middleware manager that builds the processing chain."""

from __future__ import annotations

import logging
from typing import Any

from .base import BaseMiddleware, Event, HandlerType

logger = logging.getLogger(__name__)


class MiddlewareManager:
    """Chains middlewares in reverse order, wrapping the final handler.

    Given middlewares ``[A, B, C]`` and a final handler ``H``, the
    resulting call order is::

        A -> B -> C -> H

    Each middleware calls ``await handler(event, data)`` to invoke the
    next layer.  Any middleware can short-circuit by *not* calling
    ``handler``.
    """

    def __init__(self) -> None:
        self._middlewares: list[BaseMiddleware] = []

    def add(self, middleware: BaseMiddleware) -> None:
        """Register a middleware instance."""
        logger.debug(
            "Middleware added: %s (total: %d)",
            type(middleware).__name__,
            len(self._middlewares) + 1,
        )
        self._middlewares.append(middleware)

    @property
    def middlewares(self) -> list[BaseMiddleware]:
        return list(self._middlewares)

    def wrap(self, final_handler: HandlerType) -> HandlerType:
        """Build a single callable that chains all middlewares around *final_handler*.

        Returns a coroutine function with the same signature as ``HandlerType``.
        """
        handler = final_handler
        for mw in reversed(self._middlewares):
            handler = _make_layer(mw, handler)
        logger.debug("Middleware chain built (%d layers)", len(self._middlewares))
        return handler


def _make_layer(
    middleware: BaseMiddleware,
    next_handler: HandlerType,
) -> HandlerType:
    """Create a closure that calls *middleware* with *next_handler*."""

    async def layer(event: Event, data: dict[str, Any]) -> Any:
        return await middleware(next_handler, event, data)

    return layer

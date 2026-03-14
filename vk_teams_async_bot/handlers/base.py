"""Base handler with filter checking and dependency injection support."""

from __future__ import annotations

import inspect
import typing
from typing import Any, Callable, Sequence

from ..filters.base import FilterBase
from ..filters.state import StateFilter
from ..types.event import BaseEvent


class BaseHandler:
    """Base handler that checks filters and executes a callback.

    Supports dependency injection: the callback's type-annotated parameters
    are resolved against bot.depends at call time. Supports regular functions,
    coroutine functions, and async generators as dependencies.
    """

    def __init__(
        self,
        callback: Callable[..., Any],
        filters: FilterBase | Sequence[FilterBase] | None = None,
    ) -> None:
        self.callback = callback
        self.filters = filters

    def check(self, event: BaseEvent) -> bool:
        """Check if this handler should handle the event.

        Returns True if no filters are set or all filters pass.
        Raises NotImplementedError if a StateFilter is encountered
        (use check_async instead).
        """
        if not self.filters:
            return True
        if isinstance(self.filters, FilterBase):
            return self.filters(event)
        return all(f(event) for f in self.filters)

    async def check_async(self, event: BaseEvent) -> bool:
        """Async check that supports StateFilter.

        Falls back to synchronous check for non-async filters.
        """
        if not self.filters:
            return True

        filters: Sequence[FilterBase]
        if isinstance(self.filters, FilterBase):
            filters = [self.filters]
        else:
            filters = self.filters

        for f in filters:
            if isinstance(f, StateFilter):
                if not await f.check(event):
                    return False
            else:
                if not f(event):
                    return False
        return True

    def has_async_filters(self) -> bool:
        """Return True if any filter requires async checking."""
        if not self.filters:
            return False
        if isinstance(self.filters, FilterBase):
            return isinstance(self.filters, StateFilter)
        return any(isinstance(f, StateFilter) for f in self.filters)

    async def check_signature(self, bot: Any) -> dict[str, Any]:
        """DI: inspect callback signature and resolve dependencies from bot.depends.

        For each parameter in the callback signature, checks if its type
        annotation matches any entry in bot.depends. Supports Annotated types.
        """
        signature = inspect.signature(self.callback)
        depends: dict[str, Any] = {}

        for key, value in signature.parameters.items():
            annotation = value.annotation
            if annotation is inspect.Parameter.empty:
                continue

            if typing.get_origin(annotation) is typing.Annotated:
                annotation = typing.get_args(annotation)[1]

            if not hasattr(bot, "depends"):
                continue

            depend = [d for d in bot.depends if d == annotation]
            if depend:
                depends[key] = annotation

        return depends

    async def handle(self, event: BaseEvent, bot: Any) -> None:
        """Execute the callback with DI resolution.

        Resolves dependencies (sync functions, coroutine functions,
        async generators) and passes them as kwargs to the callback.
        Async generators are properly closed in a finally block.
        """
        handle_kwargs = await self.check_signature(bot)

        objects: dict[str, Any] = {}
        async_generators: list[Any] = []
        try:
            for item_name, item_func in handle_kwargs.items():
                if inspect.isasyncgenfunction(item_func):
                    item = item_func()
                    async_generators.append(item)
                    objects[item_name] = await anext(item)
                    continue
                if inspect.iscoroutinefunction(item_func):
                    objects[item_name] = await item_func()
                    continue
                if inspect.isfunction(item_func):
                    objects[item_name] = item_func()
            await self.callback(event, bot, **objects)
        finally:
            for gen in async_generators:
                await gen.aclose()

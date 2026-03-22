"""Base handler with filter checking and dependency injection support."""

from __future__ import annotations

import asyncio
import inspect
import logging
import typing
from typing import Any, Callable, Sequence

from ..filters.base import FilterBase
from ..filters.state import StateFilter
from ..types.event import BaseEvent

logger = logging.getLogger(__name__)

_SENTINEL = object()
_DI_CLEANUP_TIMEOUT: float = 5.0


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
        self._cached_sig: inspect.Signature | None = None

    def _get_signature(self) -> inspect.Signature:
        """Return cached inspect.signature for the callback."""
        if self._cached_sig is None:
            self._cached_sig = inspect.signature(self.callback)
        return self._cached_sig

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
        """Async check that supports StateFilter inside composite filters."""
        if not self.filters:
            return True

        if isinstance(self.filters, FilterBase):
            return await self.filters.check_async(event)

        for f in self.filters:
            if not await f.check_async(event):
                return False
        return True

    def has_async_filters(self) -> bool:
        """Return True if any filter requires async checking."""
        if not self.filters:
            return False
        if isinstance(self.filters, FilterBase):
            return any(isinstance(f, StateFilter) for f in self.filters.iter_filters())
        return any(
            isinstance(leaf, StateFilter)
            for f in self.filters
            for leaf in f.iter_filters()
        )

    async def check_signature(self, bot: Any) -> dict[str, Any]:
        """DI: inspect callback signature and resolve dependencies from bot.depends.

        For each parameter in the callback signature, checks if its type
        annotation matches any entry in bot.depends. Supports Annotated types.
        """
        signature = self._get_signature()
        depends: dict[str, Any] = {}

        for key, value in signature.parameters.items():
            annotation = value.annotation
            if annotation is inspect.Parameter.empty:
                continue

            if typing.get_origin(annotation) is typing.Annotated:
                annotation = typing.get_args(annotation)[1]

            if not hasattr(bot, "depends"):
                continue

            for dep_func in bot.depends:
                # Direct match: annotation IS the dependency function itself
                if annotation is dep_func:
                    depends[key] = dep_func
                    break

                # Fallback: match by return type annotation
                try:
                    ret = typing.get_type_hints(dep_func).get("return")
                except (TypeError, AttributeError):
                    continue
                # For async generators, unwrap AsyncGenerator[X, Y] -> X
                origin = typing.get_origin(ret)
                if origin is not None:
                    import collections.abc

                    if origin in (
                        collections.abc.AsyncGenerator,
                        typing.AsyncGenerator,
                    ):
                        args = typing.get_args(ret)
                        if args:
                            ret = args[0]
                if ret is not None and ret is annotation:
                    depends[key] = dep_func
                    break

        if depends:
            logger.debug(
                "DI resolved for %s: %s",
                self.callback.__name__,
                list(depends.keys()),
            )
        return depends

    async def handle(
        self,
        event: BaseEvent,
        bot: Any,
        *,
        extra_kwargs: dict[str, Any] | None = None,
    ) -> None:
        """Execute the callback with DI resolution.

        Resolves dependencies (sync functions, coroutine functions,
        async generators) and passes them as kwargs to the callback.
        Async generators are properly closed in a finally block.

        ``extra_kwargs`` (e.g. fsm_context) are matched by parameter name
        against the callback signature before DI lookup.
        """
        signature = self._get_signature()
        handle_kwargs = await self.check_signature(bot)

        objects: dict[str, Any] = {}

        # Inject extra kwargs that match callback parameter names,
        # skipping positional args (event, bot) and DI-resolved deps
        positional = set(list(signature.parameters)[:2])
        if extra_kwargs:
            for param_name in signature.parameters:
                if (
                    param_name not in positional
                    and param_name not in handle_kwargs
                    and param_name in extra_kwargs
                ):
                    objects[param_name] = extra_kwargs[param_name]

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
            logger.debug("Calling handler: %s", self.callback.__name__)
            await self.callback(event, bot, **objects)
            logger.debug("Handler completed: %s", self.callback.__name__)
        finally:
            for gen in async_generators:
                try:
                    await asyncio.wait_for(gen.aclose(), timeout=_DI_CLEANUP_TIMEOUT)
                except asyncio.TimeoutError:
                    logger.warning(
                        "DI generator cleanup timed out after %.1fs",
                        _DI_CLEANUP_TIMEOUT,
                    )

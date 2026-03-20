"""Tests for MiddlewareManager chain building."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock

import pytest

from vk_teams_async_bot.middleware.base import BaseMiddleware, Event, HandlerType
from vk_teams_async_bot.middleware.manager import MiddlewareManager


class PassthroughMiddleware(BaseMiddleware):
    """Middleware that records its name and delegates to the next handler."""

    def __init__(self, name: str, log: list[str]) -> None:
        self.name = name
        self._log = log

    async def __call__(
        self,
        handler: HandlerType,
        event: Event,
        data: dict[str, Any],
    ) -> Any:
        self._log.append(f"{self.name}:before")
        result = await handler(event, data)
        self._log.append(f"{self.name}:after")
        return result


class ShortCircuitMiddleware(BaseMiddleware):
    """Middleware that never calls the next handler."""

    async def __call__(
        self,
        handler: HandlerType,
        event: Event,
        data: dict[str, Any],
    ) -> Any:
        return "short-circuited"


class InjectMiddleware(BaseMiddleware):
    """Middleware that injects a key into the data dict before calling next."""

    def __init__(self, key: str, value: Any) -> None:
        self._key = key
        self._value = value

    async def __call__(
        self,
        handler: HandlerType,
        event: Event,
        data: dict[str, Any],
    ) -> Any:
        data[self._key] = self._value
        return await handler(event, data)


class TestEmptyManager:
    async def test_empty_manager_calls_final_handler(self) -> None:
        manager = MiddlewareManager()
        handler = AsyncMock(return_value="ok")
        event = object()
        data: dict[str, Any] = {}

        wrapped = manager.wrap(handler)
        result = await wrapped(event, data)

        assert result == "ok"
        handler.assert_awaited_once_with(event, data)


class TestSingleMiddleware:
    async def test_single_middleware_wraps_handler(self) -> None:
        log: list[str] = []
        manager = MiddlewareManager()
        manager.add(PassthroughMiddleware("M", log))

        handler = AsyncMock(return_value="done")
        event = object()
        data: dict[str, Any] = {}

        wrapped = manager.wrap(handler)
        result = await wrapped(event, data)

        assert result == "done"
        handler.assert_awaited_once()
        assert log == ["M:before", "M:after"]


class TestChainOrder:
    async def test_middleware_chain_order(self) -> None:
        log: list[str] = []
        manager = MiddlewareManager()
        manager.add(PassthroughMiddleware("A", log))
        manager.add(PassthroughMiddleware("B", log))
        manager.add(PassthroughMiddleware("C", log))

        handler = AsyncMock(return_value="result")
        event = object()
        data: dict[str, Any] = {}

        wrapped = manager.wrap(handler)
        result = await wrapped(event, data)

        assert result == "result"
        handler.assert_awaited_once()
        assert log == [
            "A:before",
            "B:before",
            "C:before",
            "C:after",
            "B:after",
            "A:after",
        ]


class TestShortCircuit:
    async def test_middleware_can_short_circuit(self) -> None:
        manager = MiddlewareManager()
        manager.add(ShortCircuitMiddleware())

        handler = AsyncMock(return_value="should not reach")
        event = object()
        data: dict[str, Any] = {}

        wrapped = manager.wrap(handler)
        result = await wrapped(event, data)

        assert result == "short-circuited"
        handler.assert_not_awaited()


class TestDataInjection:
    async def test_middleware_can_inject_data(self) -> None:
        manager = MiddlewareManager()
        manager.add(InjectMiddleware("injected_key", 42))

        captured_data: dict[str, Any] = {}

        async def final_handler(event: Any, data: dict[str, Any]) -> str:
            captured_data.update(data)
            return "ok"

        event = object()
        data: dict[str, Any] = {"existing": "value"}

        wrapped = manager.wrap(final_handler)
        result = await wrapped(event, data)

        assert result == "ok"
        assert captured_data["injected_key"] == 42
        assert captured_data["existing"] == "value"


class TestMiddlewaresProperty:
    def test_middlewares_property_returns_copy(self) -> None:
        manager = MiddlewareManager()
        mw = PassthroughMiddleware("X", [])
        manager.add(mw)

        copy = manager.middlewares
        assert copy == [mw]

        # Mutating the copy should not affect the manager
        copy.append(PassthroughMiddleware("Y", []))
        assert len(manager.middlewares) == 1

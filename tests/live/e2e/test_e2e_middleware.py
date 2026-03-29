"""E2E middleware tests: middleware chain behavior with real Bot API calls."""

from __future__ import annotations

import pytest

from tests.helpers import make_new_message_event
from vk_teams_async_bot.dispatcher import Dispatcher
from vk_teams_async_bot.filters.state import StateFilter
from vk_teams_async_bot.fsm import MemoryStorage, State, StatesGroup
from vk_teams_async_bot.middleware.base import BaseMiddleware
from vk_teams_async_bot.middleware.session_timeout import SessionTimeoutMiddleware

pytestmark = pytest.mark.live


async def test_middleware_before_after_order(bot, test_user_id):
    """Middleware wraps handlers in correct before/after order."""
    dp = Dispatcher()
    log: list[str] = []

    class LogMiddleware(BaseMiddleware):
        def __init__(self, name: str) -> None:
            self.name = name

        async def __call__(self, handler, event, data):
            log.append(f"{self.name}:before")
            result = await handler(event, data)
            log.append(f"{self.name}:after")
            return result

    dp.add_middleware(LogMiddleware("A"))
    dp.add_middleware(LogMiddleware("B"))

    @dp.message()
    async def on_message(event, b):
        log.append("handler")
        await b.send_text(chat_id=test_user_id, text="E2E middleware: order test")

    event = make_new_message_event(text="hello", chat_id=test_user_id)
    await dp.feed_event(event, bot)

    assert log == ["A:before", "B:before", "handler", "B:after", "A:after"]


async def test_middleware_can_short_circuit(bot, test_user_id):
    """Middleware that returns early prevents handler from being called."""
    dp = Dispatcher()
    handler_called = False

    class BlockingMiddleware(BaseMiddleware):
        async def __call__(self, handler, event, data):
            return None

    dp.add_middleware(BlockingMiddleware())

    @dp.message()
    async def on_message(event, b):
        nonlocal handler_called
        handler_called = True

    event = make_new_message_event(text="hello", chat_id=test_user_id)
    await dp.feed_event(event, bot)

    assert not handler_called


async def test_middleware_modifies_data(bot, test_user_id):
    """Middleware injects custom data key, handler reads it."""
    dp = Dispatcher()
    injected_values: list = []

    class InjectMiddleware(BaseMiddleware):
        async def __call__(self, handler, event, data):
            data["custom_key"] = "injected_value"
            return await handler(event, data)

    dp.add_middleware(InjectMiddleware())

    @dp.message()
    async def on_message(event, b, custom_key=None):
        injected_values.append(custom_key)
        await b.send_text(chat_id=test_user_id, text="E2E middleware: data test")

    event = make_new_message_event(text="hello", chat_id=test_user_id)
    await dp.feed_event(event, bot)

    assert injected_values == ["injected_value"]


async def test_session_timeout_clears_state(bot, test_user_id):
    """SessionTimeoutMiddleware with tiny timeout clears expired state."""
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    timeout_mw = SessionTimeoutMiddleware(
        storage=storage,
        timeout=0,
        check_interval=1,
    )
    dp.add_middleware(timeout_mw)

    class Flow(StatesGroup):
        active = State()

    @dp.message(StateFilter(None, storage=storage))
    async def set_state(event, b, fsm_context):
        await fsm_context.set_state(Flow.active)

    user_id = "user_timeout"
    e1 = make_new_message_event(text="start", chat_id=test_user_id, user_id=user_id)
    await dp.feed_event(e1, bot)

    state_after = await storage.get_state((test_user_id, user_id))
    assert state_after == Flow.active.state

    await timeout_mw._cleanup_expired()

    state_cleared = await storage.get_state((test_user_id, user_id))
    assert state_cleared is None

    await timeout_mw.close()

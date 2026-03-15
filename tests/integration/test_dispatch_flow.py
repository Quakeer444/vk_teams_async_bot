"""Integration tests: full dispatch flow, middleware chain, FSMContext injection."""

from __future__ import annotations

import asyncio
from typing import Any
from unittest.mock import AsyncMock

import pytest

from vk_teams_async_bot.dispatcher import Dispatcher
from vk_teams_async_bot.filters.message import CommandFilter
from vk_teams_async_bot.filters.state import StateFilter
from vk_teams_async_bot.fsm import FSMContext, MemoryStorage, State, StatesGroup
from vk_teams_async_bot.handlers.callback_query import CallbackQueryHandler
from vk_teams_async_bot.handlers.message import MessageHandler
from vk_teams_async_bot.middleware.base import BaseMiddleware
from vk_teams_async_bot.types.event import (
    CallbackQueryEvent,
    DeletedMessageEvent,
    NewMessageEvent,
    RawUnknownEvent,
    parse_event,
)


# -- Fixtures ------------------------------------------------------------------


def _make_new_message_event(
    text: str = "hello",
    event_id: int = 1,
    chat_id: str = "chat1",
    user_id: str = "user1",
) -> NewMessageEvent:
    raw = {
        "eventId": event_id,
        "type": "newMessage",
        "payload": {
            "msgId": "msg1",
            "chat": {"chatId": chat_id, "type": "private", "title": ""},
            "from": {"userId": user_id, "firstName": "Test"},
            "text": text,
            "timestamp": 1000,
        },
    }
    event = parse_event(raw)
    assert isinstance(event, NewMessageEvent)
    return event


def _make_callback_event(
    callback_data: str = "btn1",
    event_id: int = 2,
    include_message: bool = False,
) -> CallbackQueryEvent:
    raw = {
        "eventId": event_id,
        "type": "callbackQuery",
        "payload": {
            "chat": {"chatId": "chat1", "type": "private", "title": ""},
            "from": {"userId": "user1", "firstName": "Test"},
            "queryId": "q1",
            "callbackData": callback_data,
        },
    }
    if include_message:
        raw["payload"]["message"] = {
            "msgId": "msg_in_cb",
            "from": {"userId": "user1", "firstName": "Test"},
            "text": "original message",
            "timestamp": 999,
        }
    event = parse_event(raw)
    assert isinstance(event, CallbackQueryEvent)
    return event


def _make_deleted_event(event_id: int = 3) -> DeletedMessageEvent:
    raw = {
        "eventId": event_id,
        "type": "deletedMessage",
        "payload": {
            "chat": {"chatId": "chat1", "type": "private", "title": ""},
            "msgId": "msg1",
            "timestamp": 1000,
        },
    }
    event = parse_event(raw)
    assert isinstance(event, DeletedMessageEvent)
    return event


class FakeBot:
    """Minimal bot stub for dispatch testing."""

    def __init__(self):
        self.depends: list = []


# -- Dispatch flow tests -------------------------------------------------------


class TestDispatchFlow:
    @pytest.mark.asyncio
    async def test_message_handler_called_on_new_message(self):
        dp = Dispatcher()
        callback = AsyncMock()

        dp.add_handler(MessageHandler(callback=callback))

        event = _make_new_message_event()
        await dp.feed_event(event, FakeBot())

        callback.assert_awaited_once()
        args = callback.call_args
        assert isinstance(args[0][0], NewMessageEvent)

    @pytest.mark.asyncio
    async def test_callback_handler_called_on_callback_query(self):
        dp = Dispatcher()
        callback = AsyncMock()

        dp.add_handler(CallbackQueryHandler(callback=callback))

        event = _make_callback_event()
        await dp.feed_event(event, FakeBot())

        callback.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_first_matching_handler_wins(self):
        dp = Dispatcher()
        first = AsyncMock()
        second = AsyncMock()

        dp.add_handler(MessageHandler(callback=first))
        dp.add_handler(MessageHandler(callback=second))

        event = _make_new_message_event()
        await dp.feed_event(event, FakeBot())

        first.assert_awaited_once()
        second.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_handler_not_called_for_wrong_event_type(self):
        dp = Dispatcher()
        msg_callback = AsyncMock()

        dp.add_handler(MessageHandler(callback=msg_callback))

        event = _make_deleted_event()
        await dp.feed_event(event, FakeBot())

        msg_callback.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_filter_blocks_handler(self):
        dp = Dispatcher()
        callback = AsyncMock()

        # CommandFilter expects command without "/" prefix
        dp.add_handler(
            MessageHandler(callback=callback, filters=CommandFilter("start"))
        )

        event = _make_new_message_event(text="not a command")
        await dp.feed_event(event, FakeBot())

        callback.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_filter_passes_handler(self):
        dp = Dispatcher()
        callback = AsyncMock()

        dp.add_handler(
            MessageHandler(callback=callback, filters=CommandFilter("start"))
        )

        event = _make_new_message_event(text="/start")
        await dp.feed_event(event, FakeBot())

        callback.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_unknown_event_logged_not_dispatched(self):
        dp = Dispatcher()
        callback = AsyncMock()
        dp.add_handler(MessageHandler(callback=callback))

        raw_event = RawUnknownEvent(eventId=99, type="unknownType", payload={})
        await dp.feed_event(raw_event, FakeBot())

        callback.assert_not_awaited()


# -- Decorator shortcut tests -------------------------------------------------


class TestDecoratorShortcuts:
    @pytest.mark.asyncio
    async def test_message_decorator(self):
        dp = Dispatcher()

        @dp.message()
        async def handler(event, bot):
            pass

        assert len(dp.handlers) == 1
        assert isinstance(dp.handlers[0], MessageHandler)

    @pytest.mark.asyncio
    async def test_callback_query_decorator(self):
        dp = Dispatcher()

        @dp.callback_query()
        async def handler(event, bot):
            pass

        assert len(dp.handlers) == 1
        assert isinstance(dp.handlers[0], CallbackQueryHandler)

    @pytest.mark.asyncio
    async def test_decorator_with_filter(self):
        dp = Dispatcher()
        callback = AsyncMock()

        @dp.message(CommandFilter("help"))
        async def handler(event, bot):
            pass

        assert len(dp.handlers) == 1

        dp.handlers[0].callback = callback

        event = _make_new_message_event(text="/help")
        await dp.feed_event(event, FakeBot())
        callback.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_all_decorator_shortcuts_exist(self):
        dp = Dispatcher()
        assert hasattr(dp, "message")
        assert hasattr(dp, "edited_message")
        assert hasattr(dp, "deleted_message")
        assert hasattr(dp, "pinned_message")
        assert hasattr(dp, "unpinned_message")
        assert hasattr(dp, "new_chat_members")
        assert hasattr(dp, "left_chat_members")
        assert hasattr(dp, "callback_query")


# -- Middleware chain tests ----------------------------------------------------


class LoggingMiddleware(BaseMiddleware):
    def __init__(self, name: str, log: list):
        self.name = name
        self.log = log

    async def __call__(self, handler, event, data):
        self.log.append(f"{self.name}:before")
        result = await handler(event, data)
        self.log.append(f"{self.name}:after")
        return result


class ShortCircuitMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        return None  # does NOT call handler


class TestMiddlewareChain:
    @pytest.mark.asyncio
    async def test_middleware_execution_order(self):
        dp = Dispatcher()
        log: list[str] = []

        dp.add_middleware(LoggingMiddleware("A", log))
        dp.add_middleware(LoggingMiddleware("B", log))

        @dp.message()
        async def handler(event, bot):
            log.append("handler")

        event = _make_new_message_event()
        await dp.feed_event(event, FakeBot())

        assert log == ["A:before", "B:before", "handler", "B:after", "A:after"]

    @pytest.mark.asyncio
    async def test_middleware_short_circuit(self):
        dp = Dispatcher()
        handler_called = False

        dp.add_middleware(ShortCircuitMiddleware())

        @dp.message()
        async def handler(event, bot):
            nonlocal handler_called
            handler_called = True

        event = _make_new_message_event()
        await dp.feed_event(event, FakeBot())

        assert not handler_called

    @pytest.mark.asyncio
    async def test_middleware_can_modify_data(self):
        dp = Dispatcher()

        class DataInjector(BaseMiddleware):
            async def __call__(self, handler, event, data):
                data["custom_key"] = "custom_value"
                return await handler(event, data)

        dp.add_middleware(DataInjector())

        @dp.message()
        async def handler(event, bot):
            pass

        event = _make_new_message_event()
        await dp.feed_event(event, FakeBot())


# -- FSMContext injection tests ------------------------------------------------


class TestFSMContextInjection:
    @pytest.mark.asyncio
    async def test_fsm_context_available_in_data(self):
        storage = MemoryStorage()
        dp = Dispatcher(storage=storage)
        fsm_contexts: list[FSMContext | None] = []

        class CaptureFSM(BaseMiddleware):
            async def __call__(self, handler, event, data):
                fsm_contexts.append(data.get("fsm_context"))
                return await handler(event, data)

        dp.add_middleware(CaptureFSM())

        @dp.message()
        async def handler(event, bot):
            pass

        event = _make_new_message_event()
        await dp.feed_event(event, FakeBot())

        assert len(fsm_contexts) == 1
        assert isinstance(fsm_contexts[0], FSMContext)

    @pytest.mark.asyncio
    async def test_fsm_context_state_operations(self):
        storage = MemoryStorage()
        dp = Dispatcher(storage=storage)

        class MyStates(StatesGroup):
            waiting = State()

        @dp.message(CommandFilter("start"))
        async def start_handler(event, bot, fsm_context):
            await fsm_context.set_state(MyStates.waiting)

        @dp.message()
        async def fallback(event, bot):
            pass

        event = _make_new_message_event(text="/start")
        bot = FakeBot()
        await dp.feed_event(event, bot)

        # Check state was set
        key = ("chat1", "user1")
        state = await storage.get_state(key)
        assert state == MyStates.waiting.state

    @pytest.mark.asyncio
    async def test_fsm_context_not_injected_without_storage(self):
        dp = Dispatcher()  # no storage
        fsm_contexts: list[FSMContext | None] = []

        class CaptureFSM(BaseMiddleware):
            async def __call__(self, handler, event, data):
                fsm_contexts.append(data.get("fsm_context"))
                return await handler(event, data)

        dp.add_middleware(CaptureFSM())

        @dp.message()
        async def handler(event, bot):
            pass

        event = _make_new_message_event()
        await dp.feed_event(event, FakeBot())

        assert fsm_contexts[0] is None

    @pytest.mark.asyncio
    async def test_fsm_different_chats_isolated(self):
        storage = MemoryStorage()
        dp = Dispatcher(storage=storage)

        class MyStates(StatesGroup):
            active = State()

        @dp.message()
        async def handler(event, bot, fsm_context):
            await fsm_context.set_state(MyStates.active)

        bot = FakeBot()

        event_chat1 = _make_new_message_event(chat_id="chat1", user_id="user1")
        await dp.feed_event(event_chat1, bot)

        event_chat2 = _make_new_message_event(chat_id="chat2", user_id="user1")
        await dp.feed_event(event_chat2, bot)

        state1 = await storage.get_state(("chat1", "user1"))
        state2 = await storage.get_state(("chat2", "user1"))
        assert state1 == MyStates.active.state
        assert state2 == MyStates.active.state

        # Clear one chat, other should remain
        await storage.clear(("chat1", "user1"))
        assert await storage.get_state(("chat1", "user1")) is None
        assert await storage.get_state(("chat2", "user1")) == MyStates.active.state


# -- Callback with message field tests ----------------------------------------


class TestCallbackWithMessage:
    @pytest.mark.asyncio
    async def test_callback_event_with_message_field(self):
        dp = Dispatcher()
        received_events = []

        dp.add_handler(
            CallbackQueryHandler(
                callback=AsyncMock(side_effect=lambda e, b: received_events.append(e))
            )
        )

        event = _make_callback_event(include_message=True)
        await dp.feed_event(event, FakeBot())

        assert len(received_events) == 1
        received = received_events[0]
        assert received.callback_data == "btn1"
        assert hasattr(received, "message")


# -- Stateful callback flow (FSM + callback) ----------------------------------


class TestStatefulCallbackFlow:
    @pytest.mark.asyncio
    async def test_fsm_state_set_by_message_read_by_callback(self):
        storage = MemoryStorage()
        dp = Dispatcher(storage=storage)

        class Flow(StatesGroup):
            waiting_callback = State()

        @dp.message(CommandFilter("start"))
        async def set_state(event, bot, fsm_context):
            await fsm_context.set_state(Flow.waiting_callback)

        callback_received = []

        dp.add_handler(
            CallbackQueryHandler(
                callback=AsyncMock(side_effect=lambda e, b: callback_received.append(e)),
                filters=StateFilter(Flow.waiting_callback, storage=storage),
            )
        )

        bot = FakeBot()

        msg_event = _make_new_message_event(text="/start")
        await dp.feed_event(msg_event, bot)

        cb_event = _make_callback_event(callback_data="confirm")
        await dp.feed_event(cb_event, bot)

        assert len(callback_received) == 1

    @pytest.mark.asyncio
    async def test_fsm_state_blocks_unmatched_callback(self):
        storage = MemoryStorage()
        dp = Dispatcher(storage=storage)

        class Flow(StatesGroup):
            waiting_callback = State()

        callback_received = []

        dp.add_handler(
            CallbackQueryHandler(
                callback=AsyncMock(side_effect=lambda e, b: callback_received.append(e)),
                filters=StateFilter(Flow.waiting_callback, storage=storage),
            )
        )

        bot = FakeBot()
        cb_event = _make_callback_event(callback_data="confirm")
        await dp.feed_event(cb_event, bot)

        assert len(callback_received) == 0


# -- Concurrent FSM tests -----------------------------------------------------


class TestFSMConcurrency:
    @pytest.mark.asyncio
    async def test_fsm_concurrent_different_users_no_bleed(self):
        """Prove cross-user state bleed is gone using forced interleaving."""
        storage = MemoryStorage()
        dp = Dispatcher(storage=storage)

        entered = asyncio.Event()
        proceed = asyncio.Event()

        class States(StatesGroup):
            active = State()

        @dp.message()
        async def handler(event, bot, fsm_context):
            key = (event.chat.chat_id, event.from_.user_id)
            if key == ("chat1", "user1"):
                entered.set()
                await proceed.wait()
            else:
                await entered.wait()
                proceed.set()
            await fsm_context.set_state(States.active)

        bot = FakeBot()
        e1 = _make_new_message_event(chat_id="chat1", user_id="user1")
        e2 = _make_new_message_event(chat_id="chat2", user_id="user2")

        await asyncio.gather(
            dp.feed_event(e1, bot),
            dp.feed_event(e2, bot),
        )

        assert await storage.get_state(("chat1", "user1")) == States.active.state
        assert await storage.get_state(("chat2", "user2")) == States.active.state

    @pytest.mark.asyncio
    async def test_fsm_per_user_serialization(self):
        """Prove per-user lock serializes events for same (chat, user)."""
        storage = MemoryStorage()
        dp = Dispatcher(storage=storage)
        order = []

        class States(StatesGroup):
            waiting_name = State()

        @dp.message(CommandFilter("start"))
        async def start_handler(event, bot, fsm_context):
            order.append("start_begin")
            await fsm_context.set_state(States.waiting_name)
            await asyncio.sleep(0.01)
            order.append("start_end")

        @dp.message(StateFilter(States.waiting_name, storage=storage))
        async def name_handler(event, bot, fsm_context):
            order.append("name")

        @dp.message()
        async def fallback(event, bot):
            order.append("fallback")

        bot = FakeBot()
        e1 = _make_new_message_event(text="/start", chat_id="c1", user_id="u1")
        e2 = _make_new_message_event(text="John", chat_id="c1", user_id="u1")

        await asyncio.gather(
            dp.feed_event(e1, bot),
            dp.feed_event(e2, bot),
        )

        assert order == ["start_begin", "start_end", "name"]

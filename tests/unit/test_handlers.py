"""Tests for vk_teams_async_bot.handlers package."""

# NOTE: Do NOT use 'from __future__ import annotations' here.
# The DI system relies on annotations being actual function objects,
# not lazy strings. See examples/depends.py for the usage pattern.

from functools import partial
from typing import Annotated

import aiohttp
import pytest

from vk_teams_async_bot.filters.base import FilterBase
from vk_teams_async_bot.filters.callback import CallbackDataFilter
from vk_teams_async_bot.filters.message import CommandFilter, MessageFilter, RegexpFilter
from vk_teams_async_bot.filters.state import StateFilter
from vk_teams_async_bot.fsm.state import State, StatesGroup
from vk_teams_async_bot.fsm.storage.memory import MemoryStorage
from vk_teams_async_bot.handlers.base import BaseHandler
from vk_teams_async_bot.handlers.callback_query import CallbackQueryHandler
from vk_teams_async_bot.handlers.chat_member import (
    LeftChatMembersHandler,
    NewChatMembersHandler,
)
from vk_teams_async_bot.handlers.command import CommandHandler
from vk_teams_async_bot.handlers.deleted_message import DeletedMessageHandler
from vk_teams_async_bot.handlers.edited_message import EditedMessageHandler
from vk_teams_async_bot.handlers.message import MessageHandler
from vk_teams_async_bot.handlers.pinned_message import (
    PinnedMessageHandler,
    UnpinnedMessageHandler,
)
from vk_teams_async_bot.types.enums import ChatType, EventType
from vk_teams_async_bot.types.event import (
    CallbackQueryEvent,
    DeletedMessageEvent,
    EditedMessageEvent,
    LeftChatMembersEvent,
    NewChatMembersEvent,
    NewMessageEvent,
    PinnedMessageEvent,
    UnpinnedMessageEvent,
)
from vk_teams_async_bot.types.event_chat import EventChatRef
from vk_teams_async_bot.types.user import User


# -- Helpers --


def _chat(chat_id: str = "chat1") -> EventChatRef:
    return EventChatRef(chatId=chat_id, type=ChatType.PRIVATE)


def _user(user_id: str = "user1") -> User:
    return User(userId=user_id, firstName="Alice")


def _new_message(text: str = "hello") -> NewMessageEvent:
    return NewMessageEvent(
        eventId=1,
        type=EventType.NEW_MESSAGE,
        chat=_chat(),
        **{"from": _user()},
        msgId="msg1",
        text=text,
    )


def _callback_query(callback_data: str = "btn_ok") -> CallbackQueryEvent:
    return CallbackQueryEvent(
        eventId=2,
        type=EventType.CALLBACK_QUERY,
        chat=_chat(),
        **{"from": _user()},
        queryId="q1",
        callbackData=callback_data,
    )


def _edited_message() -> EditedMessageEvent:
    return EditedMessageEvent(
        eventId=3,
        type=EventType.EDITED_MESSAGE,
        chat=_chat(),
        **{"from": _user()},
        msgId="msg1",
        text="edited",
    )


def _deleted_message() -> DeletedMessageEvent:
    return DeletedMessageEvent(
        eventId=4,
        type=EventType.DELETED_MESSAGE,
        chat=_chat(),
        msgId="msg1",
    )


def _pinned_message() -> PinnedMessageEvent:
    return PinnedMessageEvent(
        eventId=5,
        type=EventType.PINNED_MESSAGE,
        chat=_chat(),
        **{"from": _user()},
        msgId="msg1",
        text="pinned",
    )


def _unpinned_message() -> UnpinnedMessageEvent:
    return UnpinnedMessageEvent(
        eventId=6,
        type=EventType.UNPINNED_MESSAGE,
        chat=_chat(),
        msgId="msg1",
    )


def _new_chat_members() -> NewChatMembersEvent:
    return NewChatMembersEvent(
        eventId=7,
        type=EventType.NEW_CHAT_MEMBERS,
        chat=_chat(),
        newMembers=[_user("u2")],
        addedBy=_user("u1"),
    )


def _left_chat_members() -> LeftChatMembersEvent:
    return LeftChatMembersEvent(
        eventId=8,
        type=EventType.LEFT_CHAT_MEMBERS,
        chat=_chat(),
        leftMembers=[_user("u2")],
        removedBy=_user("u1"),
    )


async def _dummy_callback(event, bot):
    """No-op callback for handler tests."""
    pass


# -- handler check: each handler selects correct event type --


class TestMessageHandler:
    def test_accepts_new_message(self):
        h = MessageHandler(callback=_dummy_callback)
        assert h.check(_new_message()) is True

    def test_rejects_callback_query(self):
        h = MessageHandler(callback=_dummy_callback)
        assert h.check(_callback_query()) is False

    def test_rejects_edited(self):
        h = MessageHandler(callback=_dummy_callback)
        assert h.check(_edited_message()) is False


class TestCommandHandler:
    def test_accepts_matching_command(self):
        h = CommandHandler(callback=_dummy_callback, command="start")
        assert h.check(_new_message("/start")) is True

    def test_rejects_wrong_command(self):
        h = CommandHandler(callback=_dummy_callback, command="start")
        assert h.check(_new_message("/help")) is False

    def test_rejects_non_message(self):
        h = CommandHandler(callback=_dummy_callback, command="start")
        assert h.check(_callback_query()) is False

    def test_no_command_no_filter(self):
        h = CommandHandler(callback=_dummy_callback)
        # No filter, so base check passes; type check still applies
        assert h.check(_new_message()) is True

    def test_custom_filter_overrides_auto(self):
        f = RegexpFilter(r"^/custom$")
        h = CommandHandler(callback=_dummy_callback, command="start", filters=f)
        # Custom filter is used, not auto-generated CommandFilter
        assert h.check(_new_message("/custom")) is True
        assert h.check(_new_message("/start")) is False


class TestCallbackQueryHandler:
    def test_accepts_callback(self):
        h = CallbackQueryHandler(callback=_dummy_callback)
        assert h.check(_callback_query()) is True

    def test_rejects_message(self):
        h = CallbackQueryHandler(callback=_dummy_callback)
        assert h.check(_new_message()) is False


class TestEditedMessageHandler:
    def test_accepts_edited(self):
        h = EditedMessageHandler(callback=_dummy_callback)
        assert h.check(_edited_message()) is True

    def test_rejects_new_message(self):
        h = EditedMessageHandler(callback=_dummy_callback)
        assert h.check(_new_message()) is False


class TestDeletedMessageHandler:
    def test_accepts_deleted(self):
        h = DeletedMessageHandler(callback=_dummy_callback)
        assert h.check(_deleted_message()) is True

    def test_rejects_new_message(self):
        h = DeletedMessageHandler(callback=_dummy_callback)
        assert h.check(_new_message()) is False


class TestPinnedMessageHandler:
    def test_accepts_pinned(self):
        h = PinnedMessageHandler(callback=_dummy_callback)
        assert h.check(_pinned_message()) is True

    def test_rejects_new_message(self):
        h = PinnedMessageHandler(callback=_dummy_callback)
        assert h.check(_new_message()) is False


class TestUnpinnedMessageHandler:
    def test_accepts_unpinned(self):
        h = UnpinnedMessageHandler(callback=_dummy_callback)
        assert h.check(_unpinned_message()) is True

    def test_rejects_new_message(self):
        h = UnpinnedMessageHandler(callback=_dummy_callback)
        assert h.check(_new_message()) is False


class TestNewChatMembersHandler:
    def test_accepts_new_members(self):
        h = NewChatMembersHandler(callback=_dummy_callback)
        assert h.check(_new_chat_members()) is True

    def test_rejects_new_message(self):
        h = NewChatMembersHandler(callback=_dummy_callback)
        assert h.check(_new_message()) is False


class TestLeftChatMembersHandler:
    def test_accepts_left_members(self):
        h = LeftChatMembersHandler(callback=_dummy_callback)
        assert h.check(_left_chat_members()) is True

    def test_rejects_new_message(self):
        h = LeftChatMembersHandler(callback=_dummy_callback)
        assert h.check(_new_message()) is False


# -- Handler with filters --


class TestHandlerWithFilter:
    def test_filter_passes(self):
        f = RegexpFilter(r"hello")
        h = MessageHandler(callback=_dummy_callback, filters=f)
        assert h.check(_new_message("hello")) is True

    def test_filter_fails(self):
        f = RegexpFilter(r"goodbye")
        h = MessageHandler(callback=_dummy_callback, filters=f)
        assert h.check(_new_message("hello")) is False

    def test_callback_handler_with_filter(self):
        f = CallbackDataFilter("btn_ok")
        h = CallbackQueryHandler(callback=_dummy_callback, filters=f)
        assert h.check(_callback_query("btn_ok")) is True
        assert h.check(_callback_query("btn_cancel")) is False


class TestHandlerWithMultipleFilters:
    def test_all_pass(self):
        filters = [MessageFilter(), RegexpFilter(r"hello")]
        h = BaseHandler(callback=_dummy_callback, filters=filters)
        assert h.check(_new_message("hello")) is True

    def test_one_fails(self):
        filters = [MessageFilter(), RegexpFilter(r"goodbye")]
        h = BaseHandler(callback=_dummy_callback, filters=filters)
        assert h.check(_new_message("hello")) is False


# -- Handler async check --


class TestHandlerAsyncCheck:
    class TestStates(StatesGroup):
        waiting = State()

    @pytest.mark.asyncio
    async def test_async_check_with_state_filter(self):
        storage = MemoryStorage()
        await storage.set_state(("chat1", "user1"), "TestStates:waiting")

        f = StateFilter(self.TestStates.waiting, storage)
        h = BaseHandler(callback=_dummy_callback, filters=f)

        assert h.has_async_filters() is True
        assert await h.check_async(_new_message()) is True

    @pytest.mark.asyncio
    async def test_async_check_state_not_matching(self):
        storage = MemoryStorage()
        f = StateFilter(self.TestStates.waiting, storage)
        h = BaseHandler(callback=_dummy_callback, filters=f)

        assert await h.check_async(_new_message()) is False

    @pytest.mark.asyncio
    async def test_async_check_mixed_filters(self):
        storage = MemoryStorage()
        await storage.set_state(("chat1", "user1"), "TestStates:waiting")

        filters = [
            MessageFilter(),
            StateFilter(self.TestStates.waiting, storage),
        ]
        h = BaseHandler(callback=_dummy_callback, filters=filters)
        assert h.has_async_filters() is True
        assert await h.check_async(_new_message()) is True

    @pytest.mark.asyncio
    async def test_async_check_no_async_filters(self):
        h = MessageHandler(callback=_dummy_callback)
        assert h.has_async_filters() is False
        assert await h.check_async(_new_message()) is True


# -- Handler DI (handle method) --


class TestHandlerDI:
    @pytest.mark.asyncio
    async def test_simple_callback(self):
        """Handler calls callback with (event, bot) when no DI needed."""
        calls = []

        async def cb(event, bot):
            calls.append((event, bot))

        h = BaseHandler(callback=cb)
        event = _new_message()
        bot = _MockBot(depends=[])

        await h.handle(event, bot)
        assert len(calls) == 1
        assert calls[0][0] is event

    @pytest.mark.asyncio
    async def test_callback_with_sync_dependency(self):
        """Handler resolves sync function dependencies.

        DI pattern: the function itself is used as annotation
        (see examples/depends.py: rules: list_rules).
        """
        calls: list = []
        bot = _MockBot(depends=[_sync_dep])
        h = BaseHandler(callback=_cb_with_sync_dep(calls))
        await h.handle(_new_message(), bot)
        assert calls == [42]

    @pytest.mark.asyncio
    async def test_callback_with_async_dependency(self):
        """Handler resolves async function dependencies."""
        calls: list = []
        bot = _MockBot(depends=[_async_dep])
        h = BaseHandler(callback=_cb_with_async_dep(calls))
        await h.handle(_new_message(), bot)
        assert calls == ["async_result"]

    @pytest.mark.asyncio
    async def test_callback_with_async_generator_dependency(self):
        """Handler resolves async generator dependencies and closes them."""
        calls: list = []
        _gen_closed.clear()
        bot = _MockBot(depends=[_async_gen_dep])
        h = BaseHandler(callback=_cb_with_gen_dep(calls))
        await h.handle(_new_message(), bot)
        assert calls == ["resource_value"]
        assert _gen_closed == [True]

    @pytest.mark.asyncio
    async def test_no_depends_attribute(self):
        """Handler works with bot that has no depends attribute."""
        calls = []

        async def cb(event, bot):
            calls.append("ok")

        h = BaseHandler(callback=cb)
        await h.handle(_new_message(), object())
        assert calls == ["ok"]

    @pytest.mark.asyncio
    async def test_partial_dependency_does_not_crash(self):
        """get_type_hints on partial/lambda should not crash handler DI."""
        calls = []

        async def cb(event, bot, val: str = "default"):
            calls.append(val)

        p = partial(lambda x: x, 42)
        bot = _MockBot(depends=[p])
        h = BaseHandler(callback=cb)
        await h.handle(_new_message(), bot)
        assert calls == ["default"]

    @pytest.mark.asyncio
    async def test_callback_with_annotated_dependency(self):
        """Verify Annotated[Type, provider] DI pattern works."""
        async def get_session() -> aiohttp.ClientSession:
            return aiohttp.ClientSession()

        async def cb(
            event,
            bot,
            session: Annotated[aiohttp.ClientSession, get_session],
        ):
            pass

        handler = MessageHandler(callback=cb)
        bot = _MockBot(depends=[get_session])
        deps = await handler.check_signature(bot)
        assert "session" in deps
        assert deps["session"] is get_session


class _MockBot:
    """Minimal bot mock with depends list for DI testing."""

    def __init__(self, depends: list):
        self.depends = depends


# -- Module-level dependency functions for DI tests --
# The DI system uses the function object itself as the annotation,
# so these must be defined at module level to be referenced in signatures.


def _sync_dep():
    return 42


async def _async_dep():
    return "async_result"


_gen_closed: list = []


async def _async_gen_dep():
    try:
        yield "resource_value"
    finally:
        _gen_closed.append(True)


def _cb_with_sync_dep(calls: list):
    """Build a callback that uses _sync_dep as annotation."""

    async def cb(event, bot, val: _sync_dep):  # type: ignore[valid-type]
        calls.append(val)

    return cb


def _cb_with_async_dep(calls: list):
    """Build a callback that uses _async_dep as annotation."""

    async def cb(event, bot, val: _async_dep):  # type: ignore[valid-type]
        calls.append(val)

    return cb


def _cb_with_gen_dep(calls: list):
    """Build a callback that uses _async_gen_dep as annotation."""

    async def cb(event, bot, res: _async_gen_dep):  # type: ignore[valid-type]
        calls.append(res)

    return cb

"""Integration tests for FSM filters within the dispatcher flow."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from vk_teams_async_bot.dispatcher import Dispatcher
from vk_teams_async_bot.filters.state import StateFilter, StatesGroupFilter
from vk_teams_async_bot.fsm.state import State, StatesGroup
from vk_teams_async_bot.fsm.storage.memory import MemoryStorage
from vk_teams_async_bot.types.enums import ChatType, EventType
from vk_teams_async_bot.types.event import NewMessageEvent
from vk_teams_async_bot.types.event_chat import EventChatRef
from vk_teams_async_bot.types.user import User


class GroupA(StatesGroup):
    step1 = State()
    step2 = State()


class GroupB(StatesGroup):
    step1 = State()


def _msg(chat_id: str = "chat1", user_id: str = "user1") -> NewMessageEvent:
    return NewMessageEvent(
        eventId=1,
        type=EventType.NEW_MESSAGE,
        chat=EventChatRef(chatId=chat_id, type=ChatType.PRIVATE),
        **{"from": User(userId=user_id, firstName="Test")},
        msgId="m1",
        text="hello",
    )


def _bot() -> MagicMock:
    bot = MagicMock()
    bot.depends = {}
    return bot


class TestWildcardStateFilterDispatch:
    """StateFilter('*') matches any non-null state, rejects None."""

    @pytest.mark.asyncio
    async def test_wildcard_matches_in_state(self) -> None:
        storage = MemoryStorage()
        await storage.set_state(("chat1", "user1"), "GroupA:step1")

        dp = Dispatcher(storage=storage)
        handler = MagicMock()

        @dp.message(StateFilter("*"))
        async def on_msg(event, bot):
            handler()

        await dp.feed_event(_msg(), _bot())
        handler.assert_called_once()

    @pytest.mark.asyncio
    async def test_wildcard_rejects_no_state(self) -> None:
        storage = MemoryStorage()

        dp = Dispatcher(storage=storage)
        handler = MagicMock()

        @dp.message(StateFilter("*"))
        async def on_msg(event, bot):
            handler()

        await dp.feed_event(_msg(), _bot())
        handler.assert_not_called()


class TestStateFilterNoneDispatch:
    """StateFilter(None) matches when user has no state."""

    @pytest.mark.asyncio
    async def test_none_matches_no_state(self) -> None:
        storage = MemoryStorage()

        dp = Dispatcher(storage=storage)
        handler = MagicMock()

        @dp.message(StateFilter(None))
        async def on_msg(event, bot):
            handler()

        await dp.feed_event(_msg(), _bot())
        handler.assert_called_once()

    @pytest.mark.asyncio
    async def test_none_rejects_in_state(self) -> None:
        storage = MemoryStorage()
        await storage.set_state(("chat1", "user1"), "GroupA:step1")

        dp = Dispatcher(storage=storage)
        handler = MagicMock()

        @dp.message(StateFilter(None))
        async def on_msg(event, bot):
            handler()

        await dp.feed_event(_msg(), _bot())
        handler.assert_not_called()


class TestStatesGroupFilterDispatch:
    """StatesGroupFilter matches state in group, rejects outside group."""

    @pytest.mark.asyncio
    async def test_matches_state_in_group(self) -> None:
        storage = MemoryStorage()
        await storage.set_state(("chat1", "user1"), "GroupA:step1")

        dp = Dispatcher(storage=storage)
        handler = MagicMock()

        @dp.message(StatesGroupFilter(GroupA))
        async def on_msg(event, bot):
            handler()

        await dp.feed_event(_msg(), _bot())
        handler.assert_called_once()

    @pytest.mark.asyncio
    async def test_rejects_state_outside_group(self) -> None:
        storage = MemoryStorage()
        await storage.set_state(("chat1", "user1"), "GroupB:step1")

        dp = Dispatcher(storage=storage)
        handler = MagicMock()

        @dp.message(StatesGroupFilter(GroupA))
        async def on_msg(event, bot):
            handler()

        await dp.feed_event(_msg(), _bot())
        handler.assert_not_called()

    @pytest.mark.asyncio
    async def test_rejects_no_state(self) -> None:
        storage = MemoryStorage()

        dp = Dispatcher(storage=storage)
        handler = MagicMock()

        @dp.message(StatesGroupFilter(GroupA))
        async def on_msg(event, bot):
            handler()

        await dp.feed_event(_msg(), _bot())
        handler.assert_not_called()


class TestInjectStorageForStatesGroupFilter:
    """Dispatcher._inject_storage works with StatesGroupFilter."""

    @pytest.mark.asyncio
    async def test_storage_injected_into_group_filter(self) -> None:
        storage = MemoryStorage()
        await storage.set_state(("chat1", "user1"), "GroupA:step2")

        dp = Dispatcher(storage=storage)
        group_filter = StatesGroupFilter(GroupA)
        assert group_filter._storage is None

        handler = MagicMock()

        @dp.message(group_filter)
        async def on_msg(event, bot):
            handler()

        await dp.feed_event(_msg(), _bot())
        assert group_filter._storage is storage
        handler.assert_called_once()

    @pytest.mark.asyncio
    async def test_multiple_filters_both_injected(self) -> None:
        storage = MemoryStorage()
        await storage.set_state(("chat1", "user1"), "GroupA:step1")

        dp = Dispatcher(storage=storage)
        sf = StateFilter("*")
        gf = StatesGroupFilter(GroupA)

        handler = MagicMock()

        @dp.message(sf, gf)
        async def on_msg(event, bot):
            handler()

        await dp.feed_event(_msg(), _bot())
        assert sf._storage is storage
        assert gf._storage is storage
        handler.assert_called_once()

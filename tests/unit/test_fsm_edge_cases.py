"""Edge-case tests for FSM: State, StatesGroup, FSMContext, StateFilter."""

from __future__ import annotations

import pytest

from vk_teams_async_bot.fsm.context import FSMContext
from vk_teams_async_bot.fsm.state import State, StatesGroup
from vk_teams_async_bot.fsm.storage.memory import MemoryStorage
from vk_teams_async_bot.filters.state import StateFilter, StatesGroupFilter
from vk_teams_async_bot.types.enums import EventType
from vk_teams_async_bot.types.event import (
    DeletedMessageEvent,
    NewMessageEvent,
)
from vk_teams_async_bot.types.event_chat import EventChatRef
from vk_teams_async_bot.types.user import User


def _chat(chat_id: str = "chat1") -> EventChatRef:
    return EventChatRef(chatId=chat_id, type="private")


def _user(user_id: str = "user1") -> User:
    return User(userId=user_id, firstName="Test")


def _msg(chat_id: str = "chat1", user_id: str = "user1") -> NewMessageEvent:
    return NewMessageEvent(
        eventId=1,
        type=EventType.NEW_MESSAGE,
        chat=_chat(chat_id),
        **{"from": _user(user_id)},
        msgId="m1",
        text="hi",
    )


def _deleted_message() -> DeletedMessageEvent:
    return DeletedMessageEvent(
        eventId=2,
        type=EventType.DELETED_MESSAGE,
        chat=_chat(),
        msgId="m1",
    )


KEY = ("chat1", "user1")


# -- StatesGroup edge cases --


class TestStatesGroupInheritance:
    def test_subgroup_does_not_inherit_parent_states(self) -> None:
        class Parent(StatesGroup):
            a = State()

        class Child(Parent):
            b = State()

        parent_names = Parent.all_state_names()
        child_names = Child.all_state_names()
        assert "Parent:a" in parent_names
        assert "Child:b" in child_names
        assert "Parent:a" not in child_names


class TestEmptyStatesGroup:
    def test_empty_group(self) -> None:
        class Empty(StatesGroup):
            pass

        assert Empty.all_states() == []
        assert Empty.all_state_names() == []


class TestStateWithNone:
    def test_standalone_state_none_eq(self) -> None:
        s1 = State()
        s2 = State()
        assert s1 == s2  # both have state=None

    def test_standalone_state_none_hash(self) -> None:
        s = State()
        assert hash(s) == hash(None)

    def test_state_none_not_equal_to_string(self) -> None:
        s = State()
        assert s != "something"


class TestDuplicateStateNamesAcrossGroups:
    def test_same_attr_name_different_groups(self) -> None:
        class GroupA(StatesGroup):
            step = State()

        class GroupB(StatesGroup):
            step = State()

        assert GroupA.step.state == "GroupA:step"
        assert GroupB.step.state == "GroupB:step"
        assert GroupA.step != GroupB.step


# -- FSMContext edge cases --


class TestFSMContextEdgeCases:
    @pytest.mark.asyncio
    async def test_set_state_with_none_state_object(self) -> None:
        storage = MemoryStorage()
        ctx = FSMContext(storage=storage, key=KEY)
        s = State()  # state=None
        await ctx.set_state(s)
        assert await ctx.get_state() is None

    @pytest.mark.asyncio
    async def test_update_data_returns_merged_without_mutation(self) -> None:
        storage = MemoryStorage()
        ctx = FSMContext(storage=storage, key=KEY)
        await ctx.set_data({"a": 1})
        result = await ctx.update_data(b=2)
        assert result == {"a": 1, "b": 2}
        result["c"] = 3
        assert "c" not in await ctx.get_data()

    @pytest.mark.asyncio
    async def test_multiple_set_data_calls(self) -> None:
        storage = MemoryStorage()
        ctx = FSMContext(storage=storage, key=KEY)
        await ctx.set_data({"x": 1})
        await ctx.set_data({"y": 2})
        data = await ctx.get_data()
        assert data == {"y": 2}


# -- StateFilter edge cases --


class TestStateFilterEdgeCases:
    @pytest.mark.asyncio
    async def test_no_storage_returns_false(self) -> None:
        f = StateFilter("anything")
        assert await f.check(_msg()) is False

    @pytest.mark.asyncio
    async def test_set_storage_after_creation(self) -> None:
        storage = MemoryStorage()
        await storage.set_state(KEY, "some_state")
        f = StateFilter("some_state")
        assert await f.check(_msg()) is False
        f.set_storage(storage)
        assert await f.check(_msg()) is True

    @pytest.mark.asyncio
    async def test_check_async_equals_check(self) -> None:
        storage = MemoryStorage()
        await storage.set_state(KEY, "s")
        f = StateFilter("s", storage)
        event = _msg()
        assert await f.check(event) == await f.check_async(event)

    def test_repr(self) -> None:
        f = StateFilter("MyGroup:step")
        assert repr(f) == "StateFilter(state='MyGroup:step')"

    def test_repr_with_state_object(self) -> None:
        class G(StatesGroup):
            x = State()

        f = StateFilter(G.x)
        assert repr(f) == "StateFilter(state='G:x')"

    def test_repr_none(self) -> None:
        f = StateFilter(None)
        assert repr(f) == "StateFilter(state=None)"


# -- StateFilter("*") wildcard --


class TestStateFilterWildcard:
    @pytest.mark.asyncio
    async def test_wildcard_matches_any_state(self) -> None:
        storage = MemoryStorage()
        await storage.set_state(KEY, "SomeGroup:step")
        f = StateFilter("*", storage)
        assert await f.check(_msg()) is True

    @pytest.mark.asyncio
    async def test_wildcard_rejects_no_state(self) -> None:
        storage = MemoryStorage()
        f = StateFilter("*", storage)
        assert await f.check(_msg()) is False

    @pytest.mark.asyncio
    async def test_wildcard_via_state_object(self) -> None:
        storage = MemoryStorage()
        await storage.set_state(KEY, "any")
        f = StateFilter(State("*"), storage)
        assert await f.check(_msg()) is True


# -- StateFilter(None) --


class TestStateFilterNone:
    @pytest.mark.asyncio
    async def test_none_matches_no_state(self) -> None:
        storage = MemoryStorage()
        f = StateFilter(None, storage)
        assert await f.check(_msg()) is True

    @pytest.mark.asyncio
    async def test_none_rejects_any_state(self) -> None:
        storage = MemoryStorage()
        await storage.set_state(KEY, "SomeGroup:step")
        f = StateFilter(None, storage)
        assert await f.check(_msg()) is False

    @pytest.mark.asyncio
    async def test_event_without_user_returns_false(self) -> None:
        storage = MemoryStorage()
        f = StateFilter(None, storage)
        assert await f.check(_deleted_message()) is False


# -- StatesGroupFilter --


class TestStatesGroupFilter:
    class GroupA(StatesGroup):
        step1 = State()
        step2 = State()

    class GroupB(StatesGroup):
        waiting = State()

    @pytest.mark.asyncio
    async def test_matches_state_in_group(self) -> None:
        storage = MemoryStorage()
        await storage.set_state(KEY, "GroupA:step1")
        f = StatesGroupFilter(self.GroupA, storage)
        assert await f.check(_msg()) is True

    @pytest.mark.asyncio
    async def test_matches_second_state_in_group(self) -> None:
        storage = MemoryStorage()
        await storage.set_state(KEY, "GroupA:step2")
        f = StatesGroupFilter(self.GroupA, storage)
        assert await f.check(_msg()) is True

    @pytest.mark.asyncio
    async def test_rejects_state_outside_group(self) -> None:
        storage = MemoryStorage()
        await storage.set_state(KEY, "GroupB:waiting")
        f = StatesGroupFilter(self.GroupA, storage)
        assert await f.check(_msg()) is False

    @pytest.mark.asyncio
    async def test_rejects_no_state(self) -> None:
        storage = MemoryStorage()
        f = StatesGroupFilter(self.GroupA, storage)
        assert await f.check(_msg()) is False

    @pytest.mark.asyncio
    async def test_no_storage_returns_false(self) -> None:
        f = StatesGroupFilter(self.GroupA)
        assert await f.check(_msg()) is False

    @pytest.mark.asyncio
    async def test_event_without_user_returns_false(self) -> None:
        storage = MemoryStorage()
        f = StatesGroupFilter(self.GroupA, storage)
        assert await f.check(_deleted_message()) is False

    @pytest.mark.asyncio
    async def test_set_storage_after_creation(self) -> None:
        storage = MemoryStorage()
        await storage.set_state(KEY, "GroupA:step1")
        f = StatesGroupFilter(self.GroupA)
        assert await f.check(_msg()) is False
        f.set_storage(storage)
        assert await f.check(_msg()) is True

    @pytest.mark.asyncio
    async def test_check_async_equals_check(self) -> None:
        storage = MemoryStorage()
        await storage.set_state(KEY, "GroupA:step1")
        f = StatesGroupFilter(self.GroupA, storage)
        event = _msg()
        assert await f.check(event) == await f.check_async(event)

    def test_sync_call_raises(self) -> None:
        f = StatesGroupFilter(self.GroupA)
        with pytest.raises(NotImplementedError):
            f(_msg())

    def test_repr(self) -> None:
        f = StatesGroupFilter(self.GroupA)
        assert repr(f) == "StatesGroupFilter(group='GroupA')"

    @pytest.mark.asyncio
    async def test_empty_group_rejects_everything(self) -> None:
        class Empty(StatesGroup):
            pass

        storage = MemoryStorage()
        await storage.set_state(KEY, "anything")
        f = StatesGroupFilter(Empty, storage)
        assert await f.check(_msg()) is False
